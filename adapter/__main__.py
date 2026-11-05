# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#outil-et-manifeste
import argparse
import json
from pathlib import Path
import sys

from .archive import package
from .manifest import ManifestError,load,public_plan


def main():
    parser=argparse.ArgumentParser(description='Préparer les fonctions pour P2Enjoy Serverless.')
    parser.add_argument('command',choices=('plan','package'))
    parser.add_argument('--config',default='serverless.yml')
    parser.add_argument('--runtime',choices=('node24',))
    parser.add_argument('--accept-provider-differences',action='store_true')
    args=parser.parse_args()
    if sys.version_info<(3,13):parser.error('Python 3.13 ou plus récent requis.')
    try:
        path=Path(args.config).resolve()
        plan=load(path,args.runtime,args.accept_provider_differences)
        if args.command=='plan':print(json.dumps(public_plan(plan),ensure_ascii=False,indent=2))
        else:
            result=package(plan,path.parent,path.parent/'.serverless-p2',path)
            print(json.dumps({'service':plan['service'],'descriptor':str(path.parent/'.serverless-p2/deployment.json'),
                'functions':len(result['artifacts']),'warnings':plan['warnings'],'runtime_validation':'pending'},ensure_ascii=False,indent=2))
    except (ManifestError,OSError,UnicodeError,RecursionError) as error:
        message=str(error) if isinstance(error,ManifestError) else 'Lecture ou packaging impossible ; vérifier fichiers, accès et profondeur du manifeste.'
        print('Erreur : '+message,file=sys.stderr);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
