# Tahanan Hub hardware build. Everything under hardware/ except gen/ is generated from gen/design.py.
KPY ?= /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
OUT := build

all: sch erc pcb drc
sch:            ## schematic, symbol/footprint libraries, design.json
	cd gen && python3 schgen.py && python3 verify.py
	kicad-cli sch export netlist --format kicadsexpr -o gen/tahanan.net tahanan.kicad_sch
erc: sch        ## electrical rule check, fails on any violation
	mkdir -p $(OUT) && kicad-cli sch erc --severity-all --exit-code-violations --format report -o $(OUT)/erc.rpt tahanan.kicad_sch
pcb: sch        ## placed (unrouted) board
	cd gen && $(KPY) pcbgen.py && python3 project.py
drc: pcb        ## design rule check; unrouted nets are reported, not hidden
	mkdir -p $(OUT) && kicad-cli pcb drc --severity-all --schematic-parity --format report -o $(OUT)/drc.rpt tahanan.kicad_pcb
	cd gen && python3 drcsummary.py
docs: erc       ## schematic PDF, BOM, board drawings, STEP
	mkdir -p $(OUT) && kicad-cli sch export pdf -o $(OUT)/tahanan-schematic.pdf tahanan.kicad_sch
	cd gen && python3 bom.py
	kicad-cli pcb export pdf --mode-single -l F.Fab,F.CrtYd,Edge.Cuts,User.Drawings -o $(OUT)/tahanan-placement-top.pdf tahanan.kicad_pcb
	kicad-cli pcb export step --subst-models --no-dnp -o $(OUT)/tahanan-pcb.step tahanan.kicad_pcb
	mkdir -p ../manufacturing/drawings && cp $(OUT)/tahanan-schematic.pdf $(OUT)/tahanan-placement-top.pdf $(OUT)/erc.rpt ../manufacturing/drawings/
fab: drc        ## Gerber X2, drill, position files. Refuses to run until the board is routed and DRC-clean.
	cd gen && python3 drcsummary.py --require-clean
	mkdir -p $(OUT)/fab && kicad-cli pcb export gerbers --use-drill-file-origin -o $(OUT)/fab/ tahanan.kicad_pcb
	kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 -o $(OUT)/fab/ tahanan.kicad_pcb
	kicad-cli pcb export pos --format csv --units mm --side both --exclude-dnp -o $(OUT)/fab/tahanan-pos.csv tahanan.kicad_pcb
	kicad-cli pcb export ipc2581 -o $(OUT)/fab/tahanan.xml tahanan.kicad_pcb
.PHONY: all sch erc pcb drc docs fab
