# SPDX-License-Identifier: GPL-2.0-or-later
"""Compile the shipped QMK send function against a fake queue to check lease scope."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

@unittest.skipUnless(shutil.which('cc'), 'Native C compiler required for transport integration test')
class TransportTests(unittest.TestCase):
    def test_scope_across_retry_and_early_returns(self):
        project=Path(__file__).resolve().parents[1]
        text=(project/'source-overlay/tmk_core/protocol/chibios/usb_driver.c').read_text()
        function=text[text.index('bool usb_endpoint_in_send('):text.index('\nvoid usb_endpoint_in_flush(')]
        prelude=r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#define DUCKY_USB_WAIT_GUARD
#define USB_ACTIVE 4
#define TIME_INFINITE 0xffffffffu
#define TIME_IMMEDIATE 0
#define osalDbgCheck(x) assert(x)
#define osalSysLock() ((void)0)
#define osalSysUnlock() ((void)0)
#define osalOsRescheduleS() ((void)0)
#define bqSuspendI(x) ((void)(x))
#define obqResetI(x) ((void)(x))
#define bqResumeX(x) ((void)(x))
#define obqFlush(x) ((void)(x))
typedef unsigned sysinterval_t;
typedef struct {struct {void *usbp;size_t buffer_size;} config;bool timed_out;int obqueue;} usb_endpoint_in_t;
static unsigned state=4,begins,ends,calls,retry,allowed=1,last_timeout;
static int usbGetDriverStateI(void *p){(void)p;return state;}
static bool ducky_usb_wait_begin(void){begins++;return allowed;}
static void ducky_usb_wait_end(void){ends++;}
static size_t obqWriteTimeout(int *q,const uint8_t *d,size_t n,sysinterval_t t){
 (void)q;(void)d;last_timeout=t;calls++;return retry && calls==1?0:n;
}
'''
        tests=r'''
int main(void){
 usb_endpoint_in_t e={.config={.buffer_size=32}};uint8_t d[8]={0};
 retry=1;assert(usb_endpoint_in_send(&e,d,8,100,false));
 assert(calls==2 && begins==1 && ends==1 && e.timed_out);
 begins=ends=calls=0;state=2;
 assert(!usb_endpoint_in_send(&e,d,8,100,false));assert(!begins && !ends && !calls);
 state=4;retry=0;
 assert(usb_endpoint_in_send(&e,d,8,TIME_INFINITE,false));assert(!begins && !ends);
 begins=ends=calls=0;allowed=0;
 assert(usb_endpoint_in_send(&e,d,8,100,false));assert(begins==1 && ends==0 && last_timeout==0);
 begins=ends=calls=0;allowed=1;e.timed_out=false;
 assert(usb_endpoint_in_send(&e,d,8,100,true));assert(begins==1 && ends==1 && last_timeout==100);
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'transport.c';binary=Path(tmp)/'transport-test.exe'
            source.write_text(prelude+function+tests)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)
