# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#outil-et-manifeste
import argparse
import json
from pathlib import Path
import sys

from .archive import package
from .deploy import deploy,promote
from .manifest import ManifestError,load,public_plan


def main():
    parser=argparse.ArgumentParser(description='Préparer et déployer les fonctions P2Enjoy Serverless.')
    parser.add_argument('command',choices=('plan','package','deploy','promote'))
    parser.add_argument('--config',default='serverless.yml')
    parser.add_argument('--runtime',choices=('node24',))
    parser.add_argument('--accept-provider-differences',action='store_true')
    parser.add_argument('--service')
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
    parser.add_argument('--code-only',action='store_true',help='Publier seulement le code des fonctions déjà créées.')
    parser.add_argument('--function',dest='function_id')
    parser.add_argument('--code-hash')
    args=parser.parse_args()
    if args.command=='deploy' and not args.service:parser.error('--service UUID est requis pour deploy.')
    if args.command!='deploy' and args.service:parser.error('--service ne concerne que deploy.')
    if args.command!='deploy' and args.code_only:parser.error('--code-only ne concerne que deploy.')
    if args.command=='promote' and (not args.function_id or not args.code_hash):parser.error('--function UUID et --code-hash HASH sont requis pour promote.')
    if args.command!='promote' and (args.function_id or args.code_hash):parser.error('--function et --code-hash ne concernent que promote.')
    if sys.version_info<(3,13):parser.error('Python 3.13 ou plus récent requis.')
    if args.command=='promote':
        result=promote(args.function_id,args.code_hash)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['completed'] else 1
    try:
        path=Path(args.config).resolve()
        plan=load(path,args.runtime,args.accept_provider_differences,resolve_environment=args.command=='deploy' and not args.code_only)
        if args.command=='plan':print(json.dumps(public_plan(plan),ensure_ascii=False,indent=2))
        elif args.command=='deploy':
            if plan['warnings']:print(json.dumps({'warnings':plan['warnings']},ensure_ascii=False),file=sys.stderr)
            result=deploy(plan,path,args.service,code_only=args.code_only)
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['completed'] else 1
        else:
            result=package(plan,path.parent,path.parent/'.serverless-p2',path)
            print(json.dumps({'service':plan['service'],'descriptor':str(path.parent/'.serverless-p2/deployment.json'),
                'functions':len(result['artifacts']),'warnings':plan['warnings'],'runtime_validation':'pending'},ensure_ascii=False,indent=2))
    except (ManifestError,OSError,UnicodeError,RecursionError) as error:
        message=str(error) if isinstance(error,ManifestError) else 'Lecture ou packaging impossible ; vérifier fichiers, accès et profondeur du manifeste.'
        print('Erreur : '+message,file=sys.stderr);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
