import os, calendar, time, subprocess


def run_command(command):
    print(command)
    subprocess.run(command, shell=True, check=True)


def do_setup():
    if os.path.isdir("/tmp/docprocessor"):
        return
    os.mkdir("/tmp/docprocessor")
    return


def start_scan():
    it = 1
    while True:
        value = input("Enter number of pages or nothing to process: ")
        if (value.isnumeric()):
            try:
                run_command("/usr/bin/scanimage --format tiff --batch-start=" + str(
                    it) + " --batch-count=" + value + " --resolution 300 --mode Color")
                it += 1
            except subprocess.CalledProcessError:
                print("Error in scanimage, is the paper correctly placed?")
                continue
        else:
            process_dir(cur_dir)
            break


def process_dir(dirname):
    list_files = [f for f in os.listdir(dirname) if os.path.isfile(dirname + "/" + f) and f.endswith(".tif")]
    for file in list_files:
        process_tiff_file(dirname + "/" + file, dirname)


def process_tiff_file(tiff_file, dirname):
    basename_with_dir = os.path.splitext(tiff_file)[0]
    basename = os.path.basename(basename_with_dir)
    final_dir = dirname + "/final"

    # first, convert it to pdf
    run_command("/usr/bin/convert \"" + tiff_file + "\" \"" + basename_with_dir + ".pdf\"")

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
    # and now continue uploading the files
    # after that, delete the directory


do_setup()
while True:
    cur_dir = "/tmp/docprocessor/" + str(calendar.timegm(time.gmtime()))
    final_dir = cur_dir + "/final"
    os.mkdir(cur_dir)
    os.mkdir(final_dir)
    os.chdir(cur_dir)
    start_scan()
