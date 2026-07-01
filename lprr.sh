#!/bin/bash
for i in `ls p*.lst`; do lpr -o 'landscape sides=two-sided-long-edge cpi=12 lpi=8 page-left=18 page-top=48' -r $i; done
#
exit 0
