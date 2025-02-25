config = {
    "FFMPEG": {
        "ENCODER": "libx264",
        # "ENCODER": "libx265", or "libx264" or "libvpx-vp9" etc...
        # For GPU encoding, use "h264_nvenc" or "hevc_nvenc" for Nvidia cards
        "CRF": "23"
        # "CRF": Constant Rate Factor, 0 = lossless, 51 = worst quality
    },
    "FONT": {
        "Size": "24",    # Taille de police pour les sous-titres
        "Name": "Arial"  # Nom de la police
    }
}