Patches applied to the Home Assistant OS tree by `build.sh`.

| Patch | Purpose |
|---|---|
| `0001-rpi5-64-compile-tahanan-overlay.patch` | Adds a step to the board's `haos-hook.sh` that preprocesses `tahanan/tahanan-overlay.dts` and compiles it with the kernel build's `dtc`, then installs `tahanan.dtbo` into the boot slot's `overlays/` directory. The image build stops if the overlay does not compile |

The patch was generated against Home Assistant OS 18.5 and applies cleanly to that release's
`haos-hook.sh`. It has not been exercised in a full image build. To compile the overlay by hand
instead, use the command at the top of the `.dts` file and copy the result to the boot partition.
