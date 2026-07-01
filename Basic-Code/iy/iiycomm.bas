%include zcommon      rem june 28,1979
rem pr1 file
common  pr1.co.name$
common  pr1.debugging%
common  pr1.crt.def.file$
common  pr1.bell.used%
common  pr1.manu.used%
common  pr1.oe.used%
common  pr1.invoice.used%
common  pr1.purchasing.used%
common  pr1.any.audit.used%
common  pr1.additions.audit.used%
common  pr1.depletions.audit.used%
common  pr1.start.job.audit.used%
common  pr1.start.job.audit.summary.used%
common  pr1.end.job.audit.used%
common  pr1.end.job.audit.summary.used%
common  pr1.audit.drive$
common  pr1.bom.drive$
common  pr1.current.period$
common  pr1.to.date.period$
common  pr1.bom.indicator$
common  pr1.array.size%
common  pr1.lines.per.page%,pr1.page.length%,pr1.page.width%
common  pr1.date.mo%,pr1.date.dy%,pr1.date.yr%
common  pr1.64.col.crt%,pr1.average.used%
rem pr2 file
common  pr2.part.drive$(1)
common  pr2.lo.number$(1)
common  pr2.part.files%
common  pr2.audit.number%
common  pr2.activity.report.run%
common  pr2.part.file.sort.needed%
common  pr2.last.update$
rem dms global variables
%include zdmscomm

