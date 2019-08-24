####Dir Tool

Python script for recursively comparing/listing files.

Compatible with python versions 2 and 3, but version 3 has better support for handling unicode filenames.

######Usage
dirtools.py OPTION ARG0 ARG1 ARGN...

* list [dir] - prints filenames
* list_crc [dir] - prints filenames and calculates their CRC
* append_crc [dir] - appends files CRC to their filename (e.g. 'file[CRC].txt')
* append_crc [dir] [space] - same as above, [space] denotes the separator between filename and CRC
* move_dupls_asc [from_dir] [to_dir] - moves extra duplicate files to another directory, files compared using CRC and filesize (duplicate files from ascending order are moved, i.e. last one is not moved)
* move_dupls_desc [from_dir] [to_dir] - same as above (but duplicate files in descending order are moved, i.e. first one is not moved)
* compare_crc [dir] - checks the CRC in filename is the same as the calculated CRC
* compare_dirs [dir1] [dir2] - checks filenames, filesizes and calculated CRCs are the same in both directories