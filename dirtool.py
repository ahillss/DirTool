#!/bin/env python3

from __future__ import print_function,division
import os, sys, hashlib, zlib, time, re, shutil
import io

def recurse_dir(root,folders=True,files=True):
    out=[]

    try:
        for dirname, dirnames, filenames in os.walk(root):
            #dirname2=dirname.decode('utf-8')
            if folders:
                for subdirname in dirnames:
                    #subdirname2=subdirname.decode('utf-8')
                    p=os.path.abspath(os.path.join(dirname, subdirname))

                    if not os.path.islink(p):
                            out.append(p)

            if files:
                for filename in filenames:
                    #filename2=filename.decode('utf-8')
                    p=os.path.abspath(os.path.join(dirname, filename))

                    if not os.path.islink(p):
                            out.append(p)

        out=sorted(out)

    except Exception as e:
        print("%s, failed"%(str(e)), file=sys.stderr)

    return out

class hash_file_progress:
    def __init__(self,size_total):
        self.size_count=0
        self.size_total=size_total
        self.last=0

    def run(self, data_size):
        self.size_count+=data_size
        self.last+=data_size

        if self.last > 100000000:
            print("%.2f%%"%((self.size_count/self.size_total)*100), file=sys.stderr)
            self.last=0

def hash_file(fn, chunk_size=128, progress=None,type='crc'):
    try:
    #h=hashlib.md5()
        h = 0

        with open(fn, 'rb') as f:
            while True:
                data = f.read(chunk_size)

                if not data:
                    break

                if progress != None:
                    progress.run(len(data))

                # h.update(data)
                h = zlib.crc32(data, h)

        # return h.hexdigest()
        return "%X"%(h & 0xFFFFFFFF)
    except Exception as e:
        print('problem reading "%s".'%fn, file=sys.stderr)
        return None

def list_dir(root,hash=False,folders=True,size=False):
    start_time=time.time()
    xs=recurse_dir(root,folders=folders)
    #.decode('utf-8')
    size_sum=sum([os.path.getsize(x) for x in xs])
    hash_progress=hash_file_progress(size_sum)
    ss=[]

    for x in xs:
        try:
            a=os.path.relpath(x,root)

            if hash:
                b=hash_file(x, progress=hash_progress)

                if size:
                    sz=os.path.getsize(a)
                    ss.append('"%s" [%s] {%i}'%(a,b,sz))
                else:
                    ss.append('"%s" [%s]'%(a,b))
            else:
                if size:
                    sz=os.path.getsize(a)
                    ss.append('"%s" {%i}'%(a,sz))
                else:
                    ss.append('"%s"'%a)

        except Exception as e:
            print(e, file=sys.stderr)

    end_time=time.time()-start_time
    print("done in %g"%(end_time), file=sys.stderr)
    return ss

def append_file_crc(root,spaces=None):
    xs=recurse_dir(root,folders=False)
    size_sum=sum([os.path.getsize(x) for x in xs])
    hash_progress=hash_file_progress(size_sum)

    for x in xs:
        a=os.path.splitext(x)[0]
        b=os.path.splitext(x)[1]
        h=hash_file(x, progress=hash_progress)
        if spaces==True or (spaces==None and " " in os.path.basename(x)):
            os.rename(x,"%s [%s]%s"%(a,h,b))
        elif isinstance(spaces, str):
            os.rename(x,"%s%s[%s]%s"%(a,spaces,h,b))
        else:
            os.rename(x,"%s[%s]%s"%(a,h,b))

def remove_emptydirs(root,move=None):
    # files=recurse_dir(root, folders=False)
    # os.removedirs(root)
    # shutil.rmtree(root, ignore_errors=True)
    xs=reversed(recurse_dir(root, files=False))

    for x in xs:
        if not os.listdir(x):
            try:
                print(x)
            except Exception as e:
                #print("%s, failed to print."%(str(e)))
                print(e, file=sys.stderr)

            os.rmdir(x)

def find_duplicates(root):
    xs=recurse_dir(root,folders=False)
    size_sum=sum([os.path.getsize(x) for x in xs])
    hash_progress=hash_file_progress(size_sum)
    files=dict()

    #
    for x in xs:
        h=hash_file(x, progress=hash_progress)

        if h != None:
            s=os.path.getsize(x)
            # m=os.path.getctime(x)

            if s == 0:
                os.remove(x)
            else:
                k=(h,s)

                if k not in files.keys():
                    files[k] = []

                files[k].append(x)
                
    return files

def move_files(fromdir,todir,files):
    for x in files:
        move2=os.path.join(todir,os.path.dirname(os.path.relpath(x,fromdir)))

        if not os.path.exists(move2):
            try:
                os.makedirs(move2)
            except Exception as e:
                print(e, file=sys.stderr)
                continue
            
            if not os.path.exists(move2):
                print("problem creating '{}' for '{}'.".format(move2,x), file=sys.stderr)
                continue

        try:
            shutil.move(x, move2)
        except Exception as e:
            print(e, file=sys.stderr)
            continue

    
def remove_duplicates_keep_last(root, move):
    files=find_duplicates(root)

    #
    for k,v in files.items():
        v.sort()
        move_files(root,move,v[:-1])

    #
    remove_emptydirs(root)

def remove_duplicates_keep_first(root, move):
    files=find_duplicates(root)

    #
    for k,v in files.items():
        v.sort()
        move_files(root,move,v[1:])

    #
    remove_emptydirs(root)

def remove_duplicates_all(root, move):
    files=find_duplicates(root)

    #
    for k,v in files.items():
        if len(v) > 1:
            move_files(root,move,v)

    #
    remove_emptydirs(root)
    
def check_crc(root):
    start_time=time.time()
    xs=recurse_dir(root,folders=False)
    size_sum=sum([os.path.getsize(x) for x in xs])
    hash_progress=hash_file_progress(size_sum)
    ok=True

    for x in xs:
        try:
            a=os.path.relpath(x,root)
            b=hash_file(x, progress=hash_progress)

            if not b in a:
                ok=False
                fn=a
                fn=fn.replace('\\', '/')
                fn=fn.encode('ascii',errors='replace')
                fn=fn.decode("unicode-escape")
                print(('"%s" [%s]'%(fn,b)))

        except Exception as e:
            print(e, file=sys.stderr)

    end_time=time.time()-start_time
    print("done in %g"%(end_time), file=sys.stderr)

    if ok:
        print("\neverything is ok")
    else:
        print("\ndifferences found")


def compare_dirs(dir1, dir2):
    rs1=list_dir(dir1,hash=True,folders=False,size=True)
    rs2=list_dir(dir2,hash=True,folders=False,size=True)
    rs1Len=len(rs1)
    rs2Len=len(rs2)
    i=0
    ok=True

    while i<rs1Len and i<rs2Len :
        if rs1[i]!=rs2[i]:
            print()
            print(rs1[i])
            print(rs2[i])
            ok=False

        i=i+1

    if i!=rs1Len or i!=rs2Len:
        print("file nums different %i and %i"%(rs1Len,rs2Len))
        ok=False

    if ok:
        print("\neverything is ok")
    else:
        print("\ndifferences found")

def main():
    argsCount = len(sys.argv)

    if (sys.version_info > (3, 0)):
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), sys.stdout.encoding, 'replace')
    else:
        ""
        # sys.stdout.set_encoding (opts.encoding)
        # writer = codecs.getwriter(desired_encoding)
        # sys.stdout = writer(sys.stdout.buffer)

    if argsCount == 1:
        print("""Usage:
        list [dir]
        list_crc [dir]
        append_crc [dir]
        append_crc [dir] [space]
        move_dupls_first [from_dir] [to_dir]
        move_dupls_last [from_dir] [to_dir]
        move_dupls_all [from_dir] [to_dir]
        compare_crc [dir]
        compare_dirs [dir1] [dir2]
        """, file=sys.stderr)
    elif argsCount==3 and sys.argv[1]=="list":
        rs=list_dir(sys.argv[2],hash=False,folders=False)

        for r in rs:
            print(r)

    elif argsCount==3 and sys.argv[1]=="list_crc":
        rs=list_dir(sys.argv[2],hash=True,folders=False)

        for r in rs:
            print(r)
    elif argsCount==3 and sys.argv[1]=="append_crc":
        append_file_crc(sys.argv[2],"")
    elif argsCount==4 and sys.argv[1]=="append_crc":
        append_file_crc(sys.argv[2],sys.argv[3])
    elif argsCount==4 and sys.argv[1]=="move_dupls_first":
        remove_duplicates_keep_first(sys.argv[2],sys.argv[3])
    elif argsCount==4 and sys.argv[1]=="move_dupls_last":
        remove_duplicates_keep_last(sys.argv[2],sys.argv[3])
    elif argsCount==4 and sys.argv[1]=="move_dupls_all":
        remove_duplicates_all(sys.argv[2],sys.argv[3])
    elif argsCount==3 and sys.argv[1]=="compare_crc":
        check_crc(sys.argv[2])
    elif argsCount==4 and sys.argv[1]=="compare_dirs":
        compare_dirs(sys.argv[2],sys.argv[3])
    else:
        print("Invalid args.", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    main()
