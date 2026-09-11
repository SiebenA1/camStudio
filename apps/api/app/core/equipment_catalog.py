"""主流相机机身与镜头型号目录（供设备配置下拉选择，避免手动输入）。

按品牌分组，覆盖主流商业摄影常用机型。
"""
from __future__ import annotations

CAMERAS: list[dict] = [
    {
        "brand": "佳能 Canon",
        "models": [
            "Canon EOS R5 Mark II", "Canon EOS R5", "Canon EOS R6 Mark II", "Canon EOS R6",
            "Canon EOS R8", "Canon EOS R3", "Canon EOS R7", "Canon EOS R10", "Canon EOS R50",
            "Canon EOS 5D Mark IV", "Canon EOS 6D Mark II", "Canon EOS 90D",
        ],
    },
    {
        "brand": "索尼 Sony",
        "models": [
            "Sony Alpha 1 II", "Sony Alpha 1", "Sony Alpha 9 III", "Sony Alpha 7R V",
            "Sony Alpha 7R IV", "Sony Alpha 7 IV", "Sony Alpha 7 III", "Sony Alpha 7S III",
            "Sony Alpha 7C II", "Sony Alpha 6700", "Sony ZV-E1", "Sony ZV-E10", "Sony FX3",
        ],
    },
    {
        "brand": "尼康 Nikon",
        "models": [
            "Nikon Z9", "Nikon Z8", "Nikon Z7 II", "Nikon Z6 III", "Nikon Z6 II",
            "Nikon Z5 II", "Nikon Z5", "Nikon Z f", "Nikon Z50 II", "Nikon Z50",
            "Nikon D850", "Nikon D780",
        ],
    },
    {
        "brand": "富士 Fujifilm",
        "models": [
            "Fujifilm GFX100 II", "Fujifilm GFX100S II", "Fujifilm GFX 50S II",
            "Fujifilm X-H2S", "Fujifilm X-H2", "Fujifilm X-T5", "Fujifilm X-T4",
            "Fujifilm X-T50", "Fujifilm X-T30 II", "Fujifilm X-S20",
            "Fujifilm X100VI", "Fujifilm X100V", "Fujifilm X-Pro3",
        ],
    },
    {
        "brand": "松下 Panasonic",
        "models": [
            "Panasonic Lumix S1R II", "Panasonic Lumix S1R", "Panasonic Lumix S1",
            "Panasonic Lumix S5 II", "Panasonic Lumix S5 IIX", "Panasonic Lumix S9",
            "Panasonic Lumix GH7", "Panasonic Lumix GH6", "Panasonic Lumix G9 II",
        ],
    },
    {
        "brand": "徕卡 Leica",
        "models": ["Leica SL3", "Leica SL2-S", "Leica SL2", "Leica Q3", "Leica M11", "Leica M11 Monochrom"],
    },
    {
        "brand": "哈苏 Hasselblad",
        "models": ["Hasselblad X2D 100C", "Hasselblad 907X & CFV 100C", "Hasselblad X1D II 50C"],
    },
    {
        "brand": "飞思 Phase One",
        "models": ["Phase One XF IQ4 150MP", "Phase One XT IQ4 150MP"],
    },
]

LENSES: list[dict] = [
    {
        "brand": "佳能 Canon RF",
        "models": [
            "Canon RF 24-70mm F2.8 L IS USM", "Canon RF 28-70mm F2 L USM",
            "Canon RF 70-200mm F2.8 L IS USM", "Canon RF 15-35mm F2.8 L IS USM",
            "Canon RF 50mm F1.2 L USM", "Canon RF 85mm F1.2 L USM",
            "Canon RF 85mm F1.2 L USM DS", "Canon RF 135mm F1.8 L IS USM",
            "Canon RF 24-105mm F2.8 L IS USM Z", "Canon RF 24-105mm F4 L IS USM",
            "Canon RF 35mm F1.4 L VCM", "Canon RF 50mm F1.4 L VCM",
            "Canon RF 100mm F2.8 L MACRO IS USM", "Canon RF 35mm F1.8 MACRO IS STM",
            "Canon RF 85mm F2 MACRO IS STM", "Canon RF 24-240mm F4-6.3 IS USM",
        ],
    },
    {
        "brand": "索尼 Sony FE",
        "models": [
            "Sony FE 24-70mm F2.8 GM II", "Sony FE 24-70mm F2.8 GM",
            "Sony FE 70-200mm F2.8 GM OSS II", "Sony FE 16-35mm F2.8 GM II",
            "Sony FE 50mm F1.2 GM", "Sony FE 50mm F1.4 GM",
            "Sony FE 85mm F1.4 GM", "Sony FE 85mm F1.4 GM II",
            "Sony FE 35mm F1.4 GM", "Sony FE 135mm F1.8 GM",
            "Sony FE 24-105mm F4 G OSS", "Sony FE 55mm F1.8 ZA",
            "Sony FE 20-70mm F4 G", "Sony FE 70-200mm F4 G OSS II", "Sony FE 24-50mm F2.8 G",
        ],
    },
    {
        "brand": "尼康 Nikon Z",
        "models": [
            "Nikon Z 24-70mm f/2.8 S", "Nikon Z 24-70mm f/2.8 S II",
            "Nikon Z 70-200mm f/2.8 VR S", "Nikon Z 14-24mm f/2.8 S",
            "Nikon Z 50mm f/1.2 S", "Nikon Z 85mm f/1.2 S",
            "Nikon Z 135mm f/1.8 S Plena", "Nikon Z 35mm f/1.2 S",
            "Nikon Z 24-120mm f/4 S", "Nikon Z 85mm f/1.8 S", "Nikon Z 50mm f/1.8 S",
        ],
    },
    {
        "brand": "富士 Fujifilm XF / GF",
        "models": [
            "Fujifilm XF 16-55mm f/2.8 R LM WR II", "Fujifilm XF 50-140mm f/2.8 R LM OIS WR",
            "Fujifilm XF 56mm f/1.2 R WR", "Fujifilm XF 33mm f/1.4 R LM WR",
            "Fujifilm XF 23mm f/1.4 R LM WR", "Fujifilm XF 8-16mm f/2.8 R LM WR",
            "Fujifilm GF 45-100mm f/4 R LM OIS WR", "Fujifilm GF 110mm f/2 R LM WR",
            "Fujifilm GF 63mm f/2.8 R WR",
        ],
    },
    {
        "brand": "适马 Sigma",
        "models": [
            "Sigma 24-70mm F2.8 DG DN II Art", "Sigma 24-70mm F2.8 DG DN Art",
            "Sigma 28-105mm F2.8 DG DN Art", "Sigma 35mm F1.4 DG DN Art",
            "Sigma 50mm F1.4 DG DN Art", "Sigma 85mm F1.4 DG DN Art",
            "Sigma 70-200mm F2.8 DG DN OS Sports",
        ],
    },
    {
        "brand": "腾龙 Tamron",
        "models": [
            "Tamron 28-75mm F/2.8 Di III VXD G2", "Tamron 35-150mm F/2-2.8 Di III VXD",
            "Tamron 70-180mm F/2.8 Di III VC VXD G2", "Tamron 17-28mm F/2.8 Di III RXD",
        ],
    },
    {
        "brand": "徕卡 Leica SL",
        "models": [
            "Leica APO-Summicron-SL 35mm f/2 ASPH", "Leica Summilux-SL 50mm f/1.4 ASPH",
            "Leica Vario-Elmarit-SL 24-90mm f/2.8-4 ASPH",
        ],
    },
    {
        "brand": "哈苏 Hasselblad XCD",
        "models": ["Hasselblad XCD 38mm f/2.5", "Hasselblad XCD 55mm f/2.5", "Hasselblad XCD 90mm f/2.5", "Hasselblad XCD 45P f/4"],
    },
]


def catalog() -> dict:
    return {"cameras": CAMERAS, "lenses": LENSES}
