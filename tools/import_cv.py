# Copies the student's CV (a PDF anywhere on this computer) to assets/cv.pdf, where /setup reads it. One command the
# project already allows, so /setup asks no permission for it. Reads nothing else and sends nothing.
# usage: python3 -I tools/import_cv.py <path to your CV .pdf>
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crew as K

def main():
    if len(sys.argv) != 2: sys.exit('usage: python3 -I tools/import_cv.py <path to your CV .pdf>')
    src = os.path.abspath(os.path.expanduser(sys.argv[1].strip().strip('"\'')))
    if not os.path.isfile(src): sys.exit(f'No file at {src}. Check the path (drag the file into the terminal to paste it).')
    with open(src, 'rb') as f:
        if f.read(5) != b'%PDF-': sys.exit(f'{src} is not a PDF. Save or export your CV as a PDF first.')
    os.makedirs(K.ASSETS, exist_ok=True)
    dst = f'{K.ASSETS}/cv.pdf'
    if os.path.abspath(dst) != src: shutil.copyfile(src, dst)
    print(f'CV copied to {os.path.relpath(dst, K.STATE)} ({os.path.getsize(dst):,} bytes). Read it from there.')

if __name__ == '__main__':
    main()
