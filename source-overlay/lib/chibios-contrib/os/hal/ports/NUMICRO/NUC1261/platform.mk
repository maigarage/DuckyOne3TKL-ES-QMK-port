PLATFORMSRC := $(CHIBIOS)/os/hal/ports/common/ARMCMx/nvic.c \
               $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/NUC1261/hal_lld.c

# Required include directories.
PLATFORMINC := $(CHIBIOS)/os/hal/ports/common/ARMCMx \
               $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/NUC1261 \
               $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/LLD

# Optional platform files.
ifeq ($(USE_SMART_BUILD),yes)
HALCONF := $(strip $(shell cat $(CONFDIR)/halconf.h $(CONFDIR)/halconf_community.h | egrep -e "\#define"))
endif

# Drivers compatible with the platform.
PLATFORMSRC += $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/NUC1261/hal_pal_lld.c
PLATFORMINC += $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/LLD/GPIOv1
PLATFORMSRC += $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/NUC1261/hal_st_lld.c
PLATFORMINC += $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/LLD/TIMv1
include $(CHIBIOS_CONTRIB)/os/hal/ports/NUMICRO/LLD/USBv1/driver.mk




# Shared variables
ALLCSRC    += $(PLATFORMSRC)
ALLXASMSRC += $(PLATFORMASM)
ALLINC     += $(PLATFORMINC)
