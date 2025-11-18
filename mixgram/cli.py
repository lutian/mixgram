import argparse
from mixgram.api import encode_video, decode_video
import json
def main():
    p = argparse.ArgumentParser(prog='mixgram')
    sub = p.add_subparsers(dest='cmd')
    enc = sub.add_parser('encode'); enc.add_argument('--input','-i', required=True); enc.add_argument('--output','-o', required=True); enc.add_argument('--model','--model', default='all-MiniLM-L6-v2'); enc.add_argument('--key-file', default=None)
    dec = sub.add_parser('decode'); dec.add_argument('--input','-i', required=True); dec.add_argument('--output','-o', default=None); dec.add_argument('--key-file', default=None)
    args = p.parse_args()
    if args.cmd == 'encode':
        with open(args.input, 'r', encoding='utf-8') as f: text = f.read()
        key = None
        if args.key_file:
            with open(args.key_file,'rb') as kf: key = kf.read()
        res = encode_video(text, args.output, model_name=args.model, key=key)
        print('Encoded:', res)
    elif args.cmd == 'decode':
        key = None
        if args.key_file:
            with open(args.key_file,'rb') as kf: key = kf.read()
        res = decode_video(args.input, key=key)
        if args.output:
            with open(args.output,'w', encoding='utf-8') as outf:
                json.dump(res, outf, ensure_ascii=False, indent=2)
            print('Decoded saved to', args.output)
        else:
            print('Decoded text length', len(res['text']))


if __name__ == "__main__":
    main()