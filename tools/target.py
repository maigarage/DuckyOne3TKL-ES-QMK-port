# SPDX-License-Identifier: GPL-2.0-or-later
"""One explicitly observed board/bootloader, not a whole product-family allowlist."""
QMK_COMMIT = "7a1bbf37c5c07da4ea0a162bb139083a46ef40a1"
KEYBOARD = "ducky/one3/tkl_rgb_experimental"
QMK_ARTIFACT = "ducky_one3_tkl_rgb_experimental_via"
ORIGINAL_SHA256 = "e04458f82c1a14baa1b77fd4d63c1b9046a93fd2ed6efe5fc778fbbf87d72c59"
UPDATER_SHA256 = "ae0c326633dc2d81379d132f48cff54a0152331cf14c3aa3d3594cc46e3903d5"
UPDATER_URL = "https://cdn.shopify.com/s/files/1/0728/4382/1295/files/Ducky_One_3_TKL_RGB_V1.16.exe?v=1780890244"
EXPECTED = {"pdid": "0x01205212", "bootloader_version": 51,
            "config0": "0xf7ffff7c", "config1": "0x00033200"}
BOOT_IDS = ((0x3233, 0x8310), (0x0416, 0x3f00))
APP_ID = (0x3233, 0x8311)
STOCK_NAME = "Ducky-One3-TKL-RGB-1.16-APROM.bin"
