#!/usr/bin/env python

import sys
import time
import padkontrol as pk
import rtmidi
from rtmidi.midiutil import open_midioutput, open_midiinput

GM_OUT_MIDI_PORT = 0
PK_IN_MIDI_PORT = 1
PK_OUT_MIDI_PORT = 2

gm_midi_out, _ = open_midioutput(GM_OUT_MIDI_PORT)
pk_midi_out, _ = open_midioutput(PK_OUT_MIDI_PORT)
pk_midi_in, _ = open_midiinput(PK_IN_MIDI_PORT)

class Metronome:
    def __init__(self):
        self.next_tick = time.monotonic_ns()
        self.tick_length = 0
        self.playing = True
        self.paused = False

    def set_tempo(self, tempo):
        self.tempo = tempo
        self.tick_length = 60000000000 // tempo

    def toggle_pause(self):
        if (self.paused):
            self.next_tick = time.monotonic_ns()
        self.paused = not self.paused

    def await_tick(self):
        while self.paused or time.monotonic_ns() < self.next_tick:
            time.sleep(0.001)

        self.next_tick += self.tick_length

def send_sysex(sysex):
    pk_midi_out.send_message(sysex)

def set_tempo(tempo):
    metronome.set_tempo(tempo)
    send_sysex(pk.led(pk.string_to_sysex('%3d' % tempo)))

def toggle_pause():
    metronome.toggle_pause()
    if metronome.paused:
        send_sysex(pk.light(pk.BUTTON_HOLD, pk.LIGHT_STATE_ON))
    else:
        send_sysex(pk.light(pk.BUTTON_HOLD, pk.LIGHT_STATE_OFF))

class PadKontrolHandler(pk.PadKontrolInput):
    def on_button_down(self, button):
        if button == pk.BUTTON_PROG_CHANGE:
            metronome.playing = False
        elif button == pk.BUTTON_HOLD:
            toggle_pause()

    def on_rotary_left(self):
        set_tempo(metronome.tempo - 1)

    def on_rotary_right(self):
        set_tempo(metronome.tempo + 1)

    def on_invalid_sysex(self, sysex):
        pass

send_sysex(pk.SYSEX_NATIVE_MODE_ON)
send_sysex(pk.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
send_sysex(pk.SYSEX_NATIVE_MODE_INIT)

pk.register_input(pk_midi_in, PadKontrolHandler())

metronome = Metronome()
set_tempo(120)

tick = 0
while metronome.playing:
    metronome.await_tick()
    send_sysex(pk.light((tick - 1) % 16, False))
    gm_midi_out.send_message([0x99, 76 if tick % 4 == 0 else 77, 127])
    send_sysex(pk.light(tick % 16, pk.LIGHT_STATE_ON))
    tick += 1

send_sysex(pk.SYSEX_NATIVE_MODE_OFF)
pk_midi_in.close_port()
gm_midi_out.close_port()
pk_midi_out.close_port()
