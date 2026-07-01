#!/bin/bash
#
# Call with prtpdf filename - source file assumed without an extension.
#
# 30/11/2018 vbc - This may need more changes for printing
#                  Needs packages - enscript and ghostscript-common
#
# 12/12/2018 vbc - Changes made for A4 and letter. There is versions
#                  of this for bot A4 and Letter called:
#                  prtpdf-A4.sh and prtpdf-Letter.sh
#                  copy to prtpdf.sh the one for your location.
#                  but note the change showing sl930-Email-$1
#
# 27/06/2023 vbc - Adjusted for ACAS and invoice print sl930.
#                  YOU MUST TEST THIS script first to check it produces correct layout
#                  and if not change the setting but ONE AT A TIME.

enscript --quiet  --no-header -h -L 60 --font=Courier9@9/8 --landscape --margins=30:30:10:10 -M A4 -p - sl930-Email-$1 | ps2pdf14 - sl930-Email-$1.pdf
exit 0

