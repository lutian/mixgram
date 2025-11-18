
CHARS = [str(i) for i in range(10)] + [chr(ord('a')+i) for i in range(26)]
PALETTE = {
 '0': '#a91d1d','1': '#c33d22','2': '#d9642a','3': '#a9631d','4': '#c38d22',
 '5': '#d9bc2a','6': '#a9a91d','7': '#a8c322','8': '#9fd92a','9': '#63d92a',
 'a': '#1da91d','b': '#22c33d','c': '#2ad964','d': '#1da963','e': '#22c38d',
 'f': '#2ad9bc','g': '#1da9a9','h': '#22a8c3','i': '#2a9fd9','j': '#1d9fd9',
 'k': '#1d63d9','l': '#3d22c3','m': '#642ad9','n': '#631da9','o': '#8d22c3',
 'p': '#bc2ad9','q': '#a91da9','r': '#c322a8','s': '#d92a9f','t': '#a91d63',
 'u': '#c32257','v': '#d92a47','w': '#ff0000','x': '#00ff00','y': '#0000ff',
 'z': '#ffff00','.': '#000000',';': '#ffffff'
}
PALETTE_RGB = {k: tuple(int(v[i:i+2],16) for i in (1,3,5)) for k,v in PALETTE.items()}
