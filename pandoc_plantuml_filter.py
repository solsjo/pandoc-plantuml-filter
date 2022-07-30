#!/usr/bin/env python

"""
Pandoc filter to process code blocks with class "plantuml" into
plant-generated images.
Needs `plantuml.jar` from http://plantuml.com/.
"""

import os
import sys
import subprocess

from pandocfilters import toJSONFilter, Para, Image
from pandocfilters import get_filename4code, get_caption, get_extension

PLANTUML_BIN = os.environ.get('PLANTUML_BIN', 'plantuml')


def rel_mkdir_symlink(src, dest):
    dest_dir = os.path.dirname(dest)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if os.path.exists(dest):
        os.remove(dest)

    src = os.path.relpath(src, dest_dir)
    os.symlink(src, dest)


def plantuml(key, value, format_, meta):
    if key == 'CodeBlock':
        [[ident, classes, keyvals], code] = value

        if "plantuml" in classes:
            caption, typef, keyvals = get_caption(keyvals)

            filename = get_filename4code("plantuml", code)
            if meta.get('plantuml-format'):
                pformat = meta.get('plantuml-format', None)
                filetype = get_extension(format_, pformat['c'][0]['c'])
            else:
                filetype = get_extension(format_, "png", html="svg", latex="png")

            src = filename + '.uml'
            dest = filename + '.' + filetype

            # Generate image only once
            if not os.path.isfile(dest):
                txt = code.encode(sys.getfilesystemencoding())
                if not txt.startswith(b"@start"):
                    txt = b"@startuml\n" + txt + b"\n@enduml\n"
                with open(src, "wb") as f:
                    f.write(txt)
                try:
                    output = subprocess.check_output(
                        PLANTUML_BIN.split() +
                        ["-t" + filetype, "-p", "<", src, ">", dest], stderr=subprocess.STDOUT, shell=True,
                        universal_newlines=True)
                except subprocess.CalledProcessError as exc:
                    raise IOError(
                        f"Status : FAIL ret: {exc.returncode}\n out: {exc.output}\n err: {exc.stderr} \n std: {exc.stdout}"
                    )
                    raise exc
                sys.stderr.write('Created image ' + dest + '\n')

            # Update symlink each run
            for ind, keyval in enumerate(keyvals):
                if keyval[0] == 'plantuml-filename':
                    link = keyval[1]
                    keyvals.pop(ind)
                    rel_mkdir_symlink(dest, link)
                    dest = link
                    break

            return Para([Image([ident, [], keyvals], caption, [dest, typef])])


def main():
    toJSONFilter(plantuml)


if __name__ == "__main__":
    main()
