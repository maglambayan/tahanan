Patches applied to the Home Assistant OS tree by `build.sh`.

One patch is still to be written during bring-up: a hook in the board's `hassos-hook.sh` that compiles
`tahanan/tahanan-overlay.dts` with the kernel build's `dtc` and copies `tahanan.dtbo` into the boot
partition `overlays/` directory. Until it exists, compile the overlay by hand with the command at the
top of the `.dts` file and copy it to the boot partition.
