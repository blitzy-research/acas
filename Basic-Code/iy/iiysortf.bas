rem     june 1, 1978
rem     dimension arrays
        pad$=chr$(0)
        maxkeys%=5
        dim srt.kpos%(maxkeys%)
        dim srt.klen%(maxkeys%)
        dim srt.kad$(maxkeys%)
        dim srt.kan$(maxkeys%)
        gosub 7725              rem clear srt arrays
        goto 7799               rem goto user code

7705    rem-----fill srt fields-----------
        srt.record$=""
        srt.record$=srt.record$+srt.in.drive$
        srt.record$=srt.record$+left$(srt.in.name$+"        ",8)
        srt.record$=srt.record$+left$(srt.in.type$+"   ",3)
        srt.record$=srt.record$+srt.out.drive$
        srt.record$=srt.record$+left$(srt.out.name$+"        ",8)
        srt.record$=srt.record$+left$(srt.out.type$+"   ",3)
        srt.record$=srt.record$+pad$
        srt.record$=srt.record$+chr$(srt.rec.length%)
        srt.record$=srt.record$+chr$(255)+pad$+pad$+pad$+pad$
        srt.record$=srt.record$+chr$(srt.backup.flag%)
        srt.record$=srt.record$+chr$(srt.disk.change.flag%)
        srt.record$=srt.record$+chr$(srt.console.flag%)
        srt.record$=srt.record$+srt.work.drive$
        for srt.x%=1 to maxkeys%
                srt.record$=srt.record$+chr$(srt.kpos%(srt.x%))
                srt.record$=srt.record$+chr$(srt.klen%(srt.x%))
                srt.record$=srt.record$+srt.kad$(srt.x%)
                srt.record$=srt.record$+srt.kan$(srt.x%)
        next srt.x%
        srt.record$=srt.record$+pad$+pad$+pad$+pad$+pad$+pad$+pad$+pad$
        return


7725    rem-----clear srt arrays-----------
        for srt.x%=1 to maxkeys%
                srt.kpos%(srt.x%)=0
                srt.klen%(srt.x%)=0
                srt.kad$(srt.x%)="A"
                srt.kan$(srt.x%)="N"
        next srt.x%
        return

7799    rem     user code

