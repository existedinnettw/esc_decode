# ESC decode

```bash
uv run python -m esc_decode.esc_decode ./tests/data/decoder--250531-232808.csv -th 10 -i 0x0 0x220
```

output

```
mcu READ_WAITreg:0x0(Type), data:0xc8(Identification Register: 0x000000C8), when AL event(AL Control Register has been written, At least one SyncManager changed, )
mcu READ_WAITreg:0x0(Type), data:0xc8(Identification Register: 0x000000C8), when AL event(AL Control Register has been written, At least one SyncManager changed, )
mcu READ_WAITreg:0x120(AL Control (low)), data:0x01(AL Control: req state=Init (0x1), Error Ind Ack=0, Device ID req=0), when AL event(AL Control Register has been written, At least one SyncManager changed, )
mcu WRITEreg:0x134(AL Status Code (low)), data:0x0000(AL status code:0), when AL event(AL Control Register has been written, At least one SyncManager changed, )
mcu WRITEreg:0x130(AL Status (low)), data:0x0001(State=Init (0x1), Error Ind =0, Device ID loaded=0, ), when AL event(AL Control Register has been written, At least one SyncManager changed, )
mcu WRITEreg:0x139(ERR LED Override), data:0x10(ERR LED Override: LED code=0x0 (Off), Override=Enabled ), when AL event(AL Control Register has been written, At least one SyncManager changed, )
...
```

## release

```shell
uv run python -m nuitka --onefile --standalone --lto=yes --static-libpython=auto --assume-yes-for-downloads esc_decode/esc_decode.py --jobs=8
```
