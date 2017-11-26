import os, calendar, time, subprocess, boto3, datetime, shutil, threading


def run_command(command):
    subprocess.run(command, shell=True, check=True)


def do_setup():
    if os.path.isdir("/tmp/docprocessor"):
        return
    os.mkdir("/tmp/docprocessor")
    return


def start_scan():
    it = 1
    while True:
        value = input("Enter number of pages to process: ")
        try:
            run_command("/usr/bin/scanimage --batch-start=" + str(
                it) + " --batch-count=" + value + " --resolution 300 --mode Color")
            it += 1
            next_action = input("Continue scanning [c], process files [p], or restart [r]? ")
            if next_action == 'p':
                print("Starting process in background...")
                threading.Thread(target=process_dir, kwargs={'dirname': cur_dir}).start()
                break
            if next_action == 'r':
                shutil.rmtree(cur_dir)
                break
        except subprocess.CalledProcessError:
            print("Error in scanimage, is the paper correctly placed?")
            continue


def process_dir(dirname):
    list_files = [f for f in os.listdir(dirname) if os.path.isfile(dirname + "/" + f) and f.endswith(".pnm")]
    for file in list_files:
        process_pnm_file(dirname + "/" + file, dirname)
    final_dir = dirname + "/final"
    list_pdfs = [f for f in os.listdir(final_dir) if os.path.isfile(final_dir + "/" + f) and f.endswith(".pdf")]
    upload_files(list_pdfs, final_dir)
    shutil.rmtree(dirname)


def process_pnm_file(pnm_file, dirname):
    basename_with_dir = os.path.splitext(pnm_file)[0]
    basename = os.path.basename(basename_with_dir)
    final_dir = dirname + "/final"

    # first, convert it to pdf
    run_command("/usr/bin/convert \"" + pnm_file + "\" \"" + basename_with_dir + ".pdf\"")

    # next, shrink the pdf file
    gs_command = "gs -q -dNOPAUSE -dBATCH -dSAFER"
    gs_command += " -sDEVICE=pdfwrite"
    gs_command += " -dCompatibilityLevel=1.3"
    gs_command += " -dPDFSETTINGS=/screen"
    gs_command += " -dEmbedAllFonts=true"
    gs_command += " -dSubsetFonts=true"
    gs_command += " -dColorImageDownsampleType=/Bicubic"
    gs_command += " -dColorImageResolution=300"
    gs_command += " -dGrayImageDownsampleType=/Bicubic"
    gs_command += " -dGrayImageResolution=300"
    gs_command += " -dMonoImageDownsampleType=/Bicubic"
    gs_command += " -dMonoImageResolution=300"
    gs_command += " -sOutputFile=\"" + final_dir + "/" + basename + ".pdf\""
    gs_command += " \"" + basename_with_dir + ".pdf\""

    run_command(gs_command)

    # sometimes, the resulting file is 0 length. In that case, copy the original pdf and let's hope that one is better
    if os.path.getsize(final_dir + "/" + basename + ".pdf") == 0:
        print(final_dir + "/" + basename + ".pdf looks wrong.. Copying uncompressed file.")
        shutil.copy(basename_with_dir + ".pdf", final_dir + "/" + basename + ".pdf")

def upload_files(files, final_dir):
    client = boto3.client('s3')
    s3_path = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for file in files:
        client.upload_file(final_dir + "/" + file, os.environ['AWS_BUCKET'], s3_path + "/" + file)

do_setup()
while True:
    cur_dir = "/tmp/docprocessor/" + str(calendar.timegm(time.gmtime()))
    final_dir = cur_dir + "/final"
    os.mkdir(cur_dir)
    os.mkdir(final_dir)
    os.chdir(cur_dir)
    start_scan()
