// Init MIDI
(
s.waitForBoot;
TempoClock.default.tempo_(1);

MIDIClient.init;
MIDIClient.destinations;
~midiOut = MIDIOut(0);
~midiDestinations = MIDIClient.destinations.collect({
	|endpoint|
	endpoint.device + endpoint.name;
});

// MIDI Selection GUI
// Should work... ?

Window.closeAll;

~mainWindow = Window.new("How do you turn this on", Rect(400, 400, 512, 256));
~dropDownLabel = StaticText(~mainWindow, Rect(16, 16, 256, 16))
.align_(\left)
.stringColor_(Color.new(0,0,0,1))
.string_("MIDI Output Device:");
~midiDropdown = PopUpMenu.new(~mainWindow, Rect(16, 48, 256, 32))
.items_(~midiDestinations)
.action_({
	|self|
	var index = self.value.postln;

	~midiDropdown.item.postln;

	~midiOut = MIDIOut(index);
	~midiOut.uid.postln;
});
~mainWindow.front;


// Define the list of commands...
// Iterate to spawn synthdefs with the correct adress space
// OTOH: "sequences" will work differently from "drones"

// Either one function, with arity (?) to support creation of either seqs or drones
// But perhaps that requires a class-based approach (methods)
// Or: separate functions called on different messages

// Skriv en "stack-funktion" här också: en Routine. Kanske bara för seqs?
// Men också för "konstiga kommandon"

~clientTuning = Tuning.at(\et12);
~clientScale = Scale.chromatic(~clientTuning);

// Seq should "only" take arrays... if int, put that into an array?

OSCdef(\stop, {
	|msg|
	Pdef(\seq).stop;
}, \stop);

OSCdef(\tempo, {
	|msg|
	var tempo;
	tempo = msg[1].asInteger;
	~clientTempo.tempo_(tempo);
	msg.postln;
}, \tempo);

OSCdef(\seq, {
	|msg|
	var processed, durations, pattern;
	msg.removeAt(0); // strip out the fucking adress
	processed = msg.collect({
		|item, index|
		item.asInteger.clip2(48);
	});

	durations = processed.collect({
		rrand(0.1, 1);
	});

	Pbindef(\seq,
		\scale, ~clientScale,
		\type, \midi,
		\midicmd, \noteOn,
		\midiout, ~midiOut,
		\degree, Pseq(processed, inf),
		\octave, 5,
		\amp, 0.75,
		\sustain, Pseq(durations, inf),
		\dur, Pseq(durations, inf)
	).play;
	processed.postln;
	durations.postln;
}, \seq);

// Drone should take ints? Or arrays... for chords

OSCdef(\drone, {
	|msg|
	var processed;
	msg.removeAt(0); // strip out the fucking adress
	processed = msg.collect({
		|item, index|
		item.asInteger.clip2(11);
	});
	processed.postln;
}, \drone);

~commandTable = Dictionary.newFrom([
	"lol", 1,
	"wow", 2,
	"omg", 3,
	"lmao", 4,
	":)", 5,
	":(", 6,
	"xD", 7,
	"wtf", 8,
	"haha", 9,
	"how do you turn this on", 10
]);

OSCdef(\command_word, {
	|msg|
	var passed_message, passed_key;
	postln("Got some sonification data: " ++ msg[1]);

	// Ev en bra idé att lägga i en Routine så att inte alla MIDI-data kommer samtidigt!
	// Det är här vi ska deffera till nån sorts stack

	~commandTable.keysValuesDo({
		|key, value|
		var commandName;
		commandName = key.asString;
		if (
			commandName
			.escapeChar($))
			.escapeChar($()
			.matchRegexp(msg[1].asString), // true: substring exists
			{
				postln("Found matching command " ++ commandName);
				passed_message = commandName;
				passed_key = value.asInteger;
				passed_key.postln;
			}, { }
		);
	});

	passed_key.postln;

	// Pdef(\seq).stop;
	Pbindef(\command_word,
		\scale, ~clientScale,
		\type, \midi,
		\midicmd, \noteOn,
		\midiout, ~midiOut,
		\degree, Pseq((passed_key + (0..4)), (1..4).choose),
		\octave, 5,
		\amp, 0.75,
		\sustain, Prand([0.1, 1, 0.1], inf),
		\dur, Prand([0.1, 1, 0.1], inf)
	).play;
	Pbindef(\seq, \octave, (4..6).choose);
	TempoClock.default.tempo_(rrand(0.5,2));
	~lfo1.set(\freq, rrand(0.1, 2));
}, \command_word);

// Maybe a function that sets the tuning?
// Does tuning influence outgoing MIDI sequenced with Pbind?
// Maybe use chromatic scales with specified tuning?

// This kludge routine can pass CC

~control1 = Bus.control(s,1);

SynthDef(\lfo1, {
	|freq = 1, out|
	var sig;
	sig = SinOsc.kr(freq);
	Out.kr(out, sig);
}).add;

~lfo1 = Synth(\lfo1, [\freq, 1, \out, ~control1]);

~controlRoutine = Routine.new({ loop { 0.04.wait;
	~control1.get({|v|
		~midiOut.control(0, 0, v.linlin(-1,1,0,127).round);
	});
}}).play;

)
// Varning! Vi har nu använt en klass som är extern!!
// Får antingen be om att installera den... eller skriva en motsvarande Routine bara

//	~controlOut = BusToMIDI(~midiOut, ~control1, channel: 0);