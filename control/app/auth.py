# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/SCHEMA.md#identités
# OIDC validation, browser binding, encrypted sessions and scoped credentials.
import asyncio
import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import secrets
import time
from urllib.parse import urlencode, urlsplit
import weakref

from cryptography.fernet import InvalidToken
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import jwt
from .network import client_address

SESSION_COOKIE='__Host-p2-session'
FLOW_COOKIE='__Host-p2-flow'
SESSION_SECONDS=8*60*60
FLOW_SECONDS=600


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class Actor:
    kind: str
    id: str
    service_id: str | None = None
    rights: tuple[str,...] = ()
    functions: tuple[str,...] | None = None


# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
@dataclass(frozen=True)
class Authorization:
    actor:Actor
    credential_digest:str
    tokens_cipher:str|None=None


class Identity:
    def __init__(self,settings,db,vault):
        self.settings,self.db,self.vault=settings,db,vault
        self.http=httpx.AsyncClient(timeout=10,follow_redirects=False,trust_env=False)
        self.discovery=None
        self.keys={}
        self.keys_at=0
        self.keys_attempt_at=0
        self.key_lock=asyncio.Lock()
        self.refresh_locks=weakref.WeakValueDictionary()

    async def close(self):
        await self.http.aclose()

    async def discover(self):
        if self.discovery:return self.discovery
        try:
            r=await self.http.get(self.settings.issuer+'/.well-known/openid-configuration')
            r.raise_for_status();data=r.json()
            if data.get('issuer')!=self.settings.issuer:raise ValueError('issuer')
            for name in ('authorization_endpoint','token_endpoint','jwks_uri','end_session_endpoint'):
                parsed=urlsplit(data[name])
                if parsed.scheme!='https' or parsed.netloc!=urlsplit(self.settings.issuer).netloc or parsed.username or parsed.password:
                    raise ValueError('endpoint origin')
            self.discovery=data
            return data
        except (httpx.HTTPError,ValueError,KeyError):
            raise HTTPException(503,'Le fournisseur SSO est indisponible.') from None

    async def signing_key(self,token):
        try:
            header=jwt.get_unverified_header(token)
            if header.get('alg') not in ('RS256','ES256') or not isinstance(header.get('kid'),str):raise ValueError()
            kid=header['kid']
        except (jwt.PyJWTError,ValueError):
            raise HTTPException(401,'Jeton SSO invalide.') from None
        async with self.key_lock:
            now=time.time()
            if now-self.keys_at>300 or kid not in self.keys:
                if now-self.keys_attempt_at<2:
                    if kid not in self.keys:raise HTTPException(401,'Clé de signature SSO inconnue.')
                else:
                    self.keys_attempt_at=now
                    data=await self.discover()
                    try:
                        r=await self.http.get(data['jwks_uri']);r.raise_for_status()
                        self.keys={k['kid']:jwt.PyJWK.from_dict(k) for k in r.json()['keys']
                                   if k.get('use','sig')=='sig' and k.get('alg') in ('RS256','ES256')}
                        self.keys_at=now
                    except (httpx.HTTPError,ValueError,KeyError,jwt.PyJWTError):
                        raise HTTPException(503,'Les clés du SSO sont indisponibles.') from None
            key=self.keys.get(kid)
            if not key or key.algorithm_name!=header['alg']:raise HTTPException(401,'Clé de signature SSO inconnue.')
            return key.key,header['alg']

    async def claims(self,token,id_token=False):
        key,algorithm=await self.signing_key(token)
        try:
            claims=jwt.decode(token,key,algorithms=[algorithm],issuer=self.settings.issuer,
                audience=self.settings.client_id if id_token else None,
                options={'require':['exp','iat','iss','sub','aud' if id_token else 'azp'],
                         'verify_aud':id_token},leeway=3)
            if not id_token and claims.get('azp')!=self.settings.client_id:raise ValueError()
            if not isinstance(claims.get('sub'),str) or not claims['sub']:raise ValueError()
            return claims
        except (jwt.PyJWTError,ValueError):
            raise HTTPException(401,'Jeton SSO invalide ou expiré.') from None

    @staticmethod
    def require_roles(claims):
        realm=claims.get('realm_access')
        roles=realm.get('roles',[]) if isinstance(realm,dict) else []
        if not isinstance(roles,list) or 'verified' not in roles:
            raise HTTPException(403,'Ce compte doit être vérifié par un administrateur du SSO.')
        if 'admin' not in roles:
            raise HTTPException(403,'Cette console est réservée aux administrateurs.')

    async def exchange(self,fields):
        data=await self.discover()
        try:
            r=await self.http.post(data['token_endpoint'],data={
                'client_id':self.settings.client_id,'client_secret':self.settings.client_secret,**fields})
            if r.status_code in (400,401,403):raise HTTPException(401,'La session SSO ne peut pas être renouvelée ou créée.')
            r.raise_for_status();payload=r.json()
            if not isinstance(payload.get('access_token'),str) or str(payload.get('token_type','')).lower()!='bearer':raise ValueError()
            return payload
        except (httpx.HTTPError,ValueError):
            raise HTTPException(503,'Le fournisseur SSO est indisponible.') from None

    async def login(self,request):
        client=client_address(request,self.settings.trusted_proxies)
        data=await self.discover()
        state,verifier,nonce=(secrets.token_urlsafe(32) for _ in range(3))
        with self.db.transaction() as db:
            db.execute('DELETE FROM login_flows WHERE expires_at<=?',(time.time(),))
            previous=request.cookies.get(FLOW_COOKIE,'')
            if re.fullmatch(r'[A-Za-z0-9_-]{43}',previous):
                db.execute('DELETE FROM login_flows WHERE state_digest=?',(digest(previous),))
            db.execute('DELETE FROM sessions WHERE expires_at<=?',(time.time(),))
            now=time.time()
            db.execute('DELETE FROM login_rate WHERE window_start<=?',(now-60,))
            rate=db.execute('SELECT attempts FROM login_rate WHERE client_address=?',(client,)).fetchone()
            if rate and rate['attempts']>=30:
                raise HTTPException(429,'Trop de tentatives depuis cette adresse. Réessayez dans une minute.',headers={'Retry-After':'60'})
            if db.execute('SELECT count(*) FROM login_flows WHERE client_address=?',(client,)).fetchone()[0]>=8:
                raise HTTPException(429,'Trop de connexions en cours depuis cette adresse.',headers={'Retry-After':'60'})
            if db.execute('SELECT count(*) FROM login_flows').fetchone()[0]>=256:
                raise HTTPException(429,'Trop de connexions en cours. Réessayez dans quelques instants.')
            db.execute('INSERT INTO login_rate VALUES (?,?,1) ON CONFLICT(client_address) DO UPDATE SET attempts=attempts+1',(client,now))
            db.execute('INSERT INTO login_flows VALUES (?,?,?,?,?)',(
                digest(state),self.vault.seal(verifier),nonce,time.time()+FLOW_SECONDS,client))
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        response=RedirectResponse(data['authorization_endpoint']+'?'+urlencode({
            'client_id':self.settings.client_id,'response_type':'code','scope':'openid profile email',
            'redirect_uri':self.settings.public_url+'/auth/retour','state':state,'nonce':nonce,
            'code_challenge':challenge,'code_challenge_method':'S256'}),status_code=303)
        response.set_cookie(FLOW_COOKIE,state,max_age=FLOW_SECONDS,secure=True,httponly=True,samesite='lax',path='/')
        return response

    async def callback(self,request:Request):
        state=request.query_params.get('state','')
        cookie=request.cookies.get(FLOW_COOKIE,'')
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}',state) or not re.fullmatch(r'[A-Za-z0-9_-]{43}',cookie) or not hmac.compare_digest(state,cookie):
            raise HTTPException(401,'Le retour SSO ne correspond pas à ce navigateur.')
        with self.db.transaction() as db:
            row=db.execute('SELECT * FROM login_flows WHERE state_digest=?',(digest(state),)).fetchone()
            db.execute('DELETE FROM login_flows WHERE state_digest=?',(digest(state),))
        if not row or row['expires_at']<=time.time():raise HTTPException(401,'La connexion SSO a expiré ou a déjà été utilisée.')
        if request.query_params.get('error') or not request.query_params.get('code'):
            raise HTTPException(401,'La connexion SSO a été refusée ou annulée.')
        tokens=await self.exchange({'grant_type':'authorization_code','code':request.query_params['code'],
            'redirect_uri':self.settings.public_url+'/auth/retour','code_verifier':self.vault.open(row['verifier_cipher'])})
        if not isinstance(tokens.get('id_token'),str):raise HTTPException(401,'Le SSO n’a pas fourni de jeton d’identité.')
        identity=await self.claims(tokens['id_token'],id_token=True)
        access=await self.claims(tokens['access_token'])
        if identity['sub']!=access['sub'] or not hmac.compare_digest(str(identity.get('nonce','')).encode(),row['nonce'].encode()):
            raise HTTPException(401,'Les identités du retour SSO ne correspondent pas.')
        self.require_roles(access)
        session,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        now=time.time()
        display=str(identity.get('name') or identity.get('preferred_username') or identity['sub'])[:200]
        with self.db.transaction() as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)',(
                digest(session),identity['sub'],display,digest(csrf),self.vault.seal({'tokens':tokens,'csrf':csrf}),
                access['exp'],now,now+SESSION_SECONDS))
        response=RedirectResponse(self.settings.public_url+'/',status_code=303)
        response.delete_cookie(FLOW_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
        response.set_cookie(SESSION_COOKIE,session,max_age=SESSION_SECONDS,secure=True,httponly=True,samesite='lax',path='/')
        return response

    def revoke_session(self,key):
        with self.db.transaction() as db:db.execute('DELETE FROM sessions WHERE digest=?',(key,))

    async def session(self,request:Request):
        cookie=request.cookies.get(SESSION_COOKIE)
        if not cookie:raise HTTPException(401,'Connectez-vous à la console.')
        key=digest(cookie)
        lock=self.refresh_locks.get(key)
        if lock is None:
            lock=asyncio.Lock();self.refresh_locks[key]=lock
        async with lock:
            row=self.db.one('SELECT * FROM sessions WHERE digest=?',(key,))
            if not row or row['expires_at']<=time.time():
                if row:self.revoke_session(key)
                raise HTTPException(401,'La session a expiré.')
            try:
                payload=self.vault.open(row['tokens_cipher'])
                if row['access_expires_at']<=time.time()+10:
                    refresh=payload['tokens'].get('refresh_token')
                    if not refresh:raise HTTPException(401,'Reconnectez-vous au SSO.')
                    tokens=await self.exchange({'grant_type':'refresh_token','refresh_token':refresh})
                    claims=await self.claims(tokens['access_token']);self.require_roles(claims)
                    if claims['sub']!=row['subject']:raise HTTPException(401,'L’identité de la session a changé.')
                    if not tokens.get('refresh_token'):tokens['refresh_token']=refresh
                    payload['tokens']=tokens
                    with self.db.transaction() as db:
                        updated=db.execute('UPDATE sessions SET tokens_cipher=?,access_expires_at=? WHERE digest=? AND expires_at>?',
                            (self.vault.seal(payload),claims['exp'],key,time.time())).rowcount
                    if not updated:raise HTTPException(401,'La session a été fermée.')
                else:
                    claims=await self.claims(payload['tokens']['access_token']);self.require_roles(claims)
                if claims['sub']!=row['subject']:raise HTTPException(401,'L’identité de la session a changé.')
                if row['expires_at']<=time.time():raise HTTPException(401,'La session a expiré.')
                row['payload']=payload
                return row
            except HTTPException as exc:
                if exc.status_code in (401,403):self.revoke_session(key)
                raise
            except (InvalidToken,KeyError,ValueError):
                self.revoke_session(key)
                raise HTTPException(401,'La session ne peut pas être relue.') from None

    def csrf(self,request,row):
        supplied=request.headers.get('x-csrf-token','')
        if request.headers.get('origin')!=self.settings.public_url or not supplied or not hmac.compare_digest(digest(supplied),row['csrf_digest']):
            raise HTTPException(403,'La vérification de sécurité de cette requête a échoué.')

    async def admin(self,request,mutation=False):
        row=await self.session(request)
        actor=Actor('admin',row['subject'])
        request.state.actor=actor
        if mutation:self.csrf(request,row)
        return actor

    async def authorize(self,request,service_id,right,function_id=None):
        token=request.headers.get('x-serverless-token')
        if token is None:return await self.admin(request,mutation=request.method not in ('GET','HEAD','OPTIONS'))
        row=self.db.one('SELECT * FROM service_tokens WHERE digest=?',(digest(token),))
        if row:request.state.actor=Actor('token',row['id'],row['service_id'])
        if not row or row['revoked_at'] is not None or (row['expires_at'] is not None and row['expires_at']<=time.time()):
            raise HTTPException(401,'Le jeton du service est invalide, expiré ou révoqué.')
        rights=tuple(json.loads(row['rights_json']))
        functions=tuple(json.loads(row['function_ids_json'])) if row['function_ids_json'] is not None else None
        if row['service_id']!=service_id or right not in rights:
            raise HTTPException(403,'Ce jeton ne permet pas cette opération dans ce service.')
        if functions is not None and function_id is not None and function_id not in functions:
            raise HTTPException(403,'Cette fonction ne fait pas partie de la portée du jeton.')
        with self.db.transaction() as db:
            db.execute('UPDATE service_tokens SET last_used_at=? WHERE id=? AND revoked_at IS NULL',(time.time(),row['id']))
        return Actor('token',row['id'],service_id,rights,functions)

    async def logout(self,request):
        cookie=request.cookies.get(SESSION_COOKIE,'')
        row=self.db.one('SELECT * FROM sessions WHERE digest=?',(digest(cookie),)) if cookie else None
        if request.headers.get('origin')!=self.settings.public_url:raise HTTPException(403,'Origine de déconnexion refusée.')
        if not row:return {'signed_out':True,'sso_signed_out':False}
        request.state.actor=Actor('admin',row['subject'])
        self.csrf(request,row)
        self.revoke_session(row['digest'])
        remote_closed=True
        try:
            data=await self.discover()
            payload=self.vault.open(row['tokens_cipher'])
            r=await self.http.post(data['end_session_endpoint'],data={
                'client_id':self.settings.client_id,'client_secret':self.settings.client_secret,
                'refresh_token':payload['tokens'].get('refresh_token','')})
            remote_closed=r.status_code in (200,204)
        except (HTTPException,httpx.HTTPError,InvalidToken,KeyError,ValueError):remote_closed=False
        return {'signed_out':True,'sso_signed_out':remote_closed}

    # @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
    async def operation(self,request,service_id,right,function_id):
        actor=await self.authorize(request,service_id,right,function_id)
        if actor.kind=='token':return Authorization(actor,digest(request.headers['x-serverless-token']))
        key=digest(request.cookies[SESSION_COOKIE])
        row=self.db.one('SELECT * FROM sessions WHERE digest=?',(key,))
        if not row or row['subject']!=actor.id:raise HTTPException(401,'La session a été fermée.')
        return Authorization(actor,key,row['tokens_cipher'])

    # @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
    def recheck(self,db,authorization,service_id,right,function_id):
        actor=authorization.actor;now=time.time()
        if actor.kind=='admin':
            row=db.execute('SELECT * FROM sessions WHERE digest=?',(authorization.credential_digest,)).fetchone()
            if (not row or row['subject']!=actor.id or row['expires_at']<=now or row['access_expires_at']<=now or
                row['tokens_cipher']!=authorization.tokens_cipher):
                raise HTTPException(401,'La session a changé ou expiré pendant cette opération.')
        else:
            row=db.execute('SELECT * FROM service_tokens WHERE id=? AND digest=?',(actor.id,authorization.credential_digest)).fetchone()
            if not row or row['revoked_at'] is not None or (row['expires_at'] is not None and row['expires_at']<=now):
                raise HTTPException(401,'Le jeton du service est invalide, expiré ou révoqué.')
            functions=json.loads(row['function_ids_json']) if row['function_ids_json'] is not None else None
            if row['service_id']!=service_id or right not in json.loads(row['rights_json']) or (functions is not None and function_id not in functions):
                raise HTTPException(403,'Les droits ont changé pendant cette opération.')
