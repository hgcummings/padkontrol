#!/usr/bin/env python

import sys
import time
import padkontrol as pk
import rtmidi
from rtmidi.midiutil import open_midioutput, open_midiinput

GM_OUT_MIDI_PORT = 0
PK_IN_MIDI_PORT = 1
PK_OUT_MIDI_PORT = 2

playing = True

gm_midi_out, _ = open_midioutput(GM_OUT_MIDI_PORT)
pk_midi_out, _ = open_midioutput(PK_OUT_MIDI_PORT)
pk_midi_in, _ = open_midiinput(PK_IN_MIDI_PORT)

class Metronome:
    def __init__(self, tempo):
        self.next_tick = time.monotonic_ns()
        self.tick_length = 0
        self.set_tempo(tempo)
        self.playing = True

    def set_tempo(self, tempo):
        self.tempo = tempo
        self.next_tick -= self.tick_length
        self.tick_length = 60000000000 // tempo
        self.next_tick += self.tick_length

    def await_tick(self):
        while time.monotonic_ns() < metronome.next_tick:
            time.sleep(0.001)

        self.next_tick += self.tick_length

def send_sysex(sysex):
    pk_midi_out.send_message(sysex)

def display_tempo():
    send_sysex(pk.led(pk.string_to_sysex('%3d' % metronome.tempo)))

send_sysex(pk.SYSEX_NATIVE_MODE_ON)
send_sysex(pk.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
send_sysex(pk.SYSEX_NATIVE_MODE_INIT)

metronome = Metronome(120)
display_tempo()

class PadKontrolHandler(pk.PadKontrolInput):
    def on_button_down(self, button):
        if button == pk.BUTTON_PROG_CHANGE:
            metronome.playing = False

    def on_rotary_left(self):
        metronome.set_tempo(metronome.tempo - 1)
        display_tempo()

    def on_rotary_right(self):
        metronome.set_tempo(metronome.tempo + 1)
        display_tempo()

    def on_invalid_sysex(self, sysex):
        pass

pk.register_input(pk_midi_in, PadKontrolHandler())

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
