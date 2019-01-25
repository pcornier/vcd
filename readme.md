### Usage:

```
$ python vcd.py
> l dump.vcd
loaded
>
> ss
Signals:
sim:my8bit:rom0:clk
sim:my8bit:bus0:rom
sim:my8bit:bus0:ram
sim:my8bit:tristate1:tin
sim:my8bit:tristate0:tin
sim:my8bit:tristate1:ena
sim:my8bit:tristate0:ena
sim:my8bit:rom0:adl
sim:my8bit:rom0:adh
sim:my8bit:ctrl_sel
sim:my8bit:bus0:dout
sim:my8bit:ram0:we
sim:my8bit:ram0:din
sim:my8bit:processor0:cycle
sim:my8bit:processor0:ps
sim:my8bit:processor0:pout
sim:my8bit:processor0:pc
>
> a sim:my8bit:rom0:clk sim:my8bit:processor0:cycle
Signals added
>
> p

       0         10        20        30        40

clk  : __________/‾‾‾‾‾‾‾‾‾\_________/‾‾‾‾‾‾‾‾‾\________

cycle: ╳ FETCH_OPC

> f
            10        20        30        40        50

clk  : _____/‾‾‾‾‾‾‾‾‾\_________/‾‾‾‾‾‾‾‾‾\_________/‾‾‾

cycle:                                              ╳ FETCH_ADR

> sc
saved signal configuration
> r
reloaded
> q
$
```

Created for my personal use for debugging MyHDL in Ternux while driving.

Commands are:
- a: add a specific signal
- aa: add all signals
- da: delete all signals
- f: time + 5
- lc: load configuration
- p: print signals
- q: quit
- r: reload vcd file
- r start end: set time range
- s: list signals
- sc: save configuration
- ss: list signals (listing format)





