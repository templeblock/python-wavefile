#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2012 David García Garzón

This file is part of python-wavefile

python-wavefile is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

python-wavefile is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
sys.path.append("../")

from wavefile import *
import unittest
import numpy as np
from numpy.testing import assert_equal as np_assert_equal

class MultiChannelDiffTests(unittest.TestCase) :

	def setUp(self) :
		self.filestoremove = []

	def tearDown(self) :
		import os
		for file in self.filestoremove :
			if os.access(file, os.F_OK) :
				os.remove(file)

	def toRemove(self, file) :
		self.filestoremove.append(file)

	def savewav(self, data, filename, samplerate) :
		import os
		assert not os.access(filename, os.F_OK), "Test temporary file already existed: %s"%filename
		import wavefile
		with wavefile.WaveWriter(
				filename,
				samplerate=samplerate,
				channels=data.shape[1]
				) as writer :
			writer.write(data.ravel("C").reshape(data.shape))
		self.toRemove(filename)

	def writeFile(self, name, content) :
		f = open(name,'w')
		self.toRemove(name)
		f.write(content)
		f.close()

	def display(self, file) :
		import os
		os.system("sweep '%s'"%file)

	def sinusoid(self, samples=400, f=440, samplerate=44100) :
		return np.sin( np.linspace(0, 2*np.pi*f*samples/samplerate, samples))[:,np.newaxis]

	def channels(self, *args) :
		return np.concatenate(args, axis=1)

	def stereoSinusoids(self, samples=400) :
		return self.channels(
			self.sinusoid(samples, 440),
			self.sinusoid(samples, 880),
			)

	def test_reader_withMissingFile(self) :
		try :
			r = wavefile.WaveReader("notexisting.wav")
			self.fail("Exception expected")
		except IOError, e :
			self.assertEqual( (
				"Error opening 'notexisting.wav': System error.",
			), e.args)

	def test_reader_withWrongfile(self) :
		self.writeFile("badfile.wav","Bad content")
		try :
			r = wavefile.WaveReader("badfile.wav")
			self.fail("Exception expected")
		except IOError, e :
			self.assertEqual( (
				"Error opening 'badfile.wav': File contains data in an unknown format.",
			), e.args)



class caca :
	# Missing files

	def test_comparewaves_missingExpected(self) :
		data = self.stereoSinusoids()

		self.savewav(data, "data2.wav", 44100)
		self.assertEquals([
			'Expected samplerate was 0 but got 44100',
			'Expected channels was 0 but got 2',
			'Expected frames was 0 but got 400',
			], differences("data1.wav", "data2.wav"))

	def test_comparewaves_missingResult(self) :
		data = self.stereoSinusoids()

		self.savewav(data, "data1.wav", 44100)
		self.assertEquals([
			'Expected samplerate was 44100 but got 0',
			'Expected channels was 2 but got 0',
			'Expected frames was 400 but got 0',
			], differences("data1.wav", "data2.wav"))


	# Structural differences

	def test_comparewaves_differentChannels(self) :
		data = self.stereoSinusoids()

		self.savewav(data[:,0:1],  "data1.wav", 44100)
		self.savewav(data,         "data2.wav", 44100)
		self.assertEquals([
			'Expected channels was 1 but got 2',
			], differences("data1.wav", "data2.wav"))

	def test_comparewaves_differentSampleRate(self) :
		data = self.stereoSinusoids()

		self.savewav(data, "data1.wav", 44100)
		self.savewav(data, "data2.wav", 48000)
		self.assertEquals([
			'Expected samplerate was 44100 but got 48000',
			], differences("data1.wav", "data2.wav"))

	def test_comparewaves_differentLenght(self) :
		data = self.sinusoid(400, 440, 44100)

		self.savewav(data,       "data1.wav", 44100)
		self.savewav(data[:200], "data2.wav", 44100)
		self.assertEquals([
			'Expected frames was 400 but got 200',
			], differences("data1.wav", "data2.wav"))

	# Helper assert for non-structural differences tests

	def assertReportEqual(self, data1, data2, expectedMessages) :
		self.savewav(data1, "data1.wav", 44100)
		self.savewav(data2, "data2.wav", 44100)
		self.assertEquals(expectedMessages,
			differences("data1.wav", "data2.wav"))

	# No differences

	def test_comparewaves_identicalMono(self) :
		data = self.sinusoid(1024, 440, 44100)

		self.assertReportEqual(data, data, [])

	def test_comparewaves_notAFullHop(self) :
		data = self.sinusoid(400, 440, 44100)

		self.assertReportEqual(data, data, [])

	def test_comparewaves_identicalStereo(self) :
		data = self.stereoSinusoids()

		self.assertReportEqual(data, data, [])

	# Content differences

	def test_comparewaves_diferentValues(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data2[50,1] = 0

		self.assertReportEqual(data1, data2, [
			"Value missmatch at channel 1, maximum difference of 0.001464 at sample 50",
			])

	def test_comparewaves_diferentValuesNextHops(self) :
		data1 = self.stereoSinusoids(samples=2000)
		data2 = data1.copy()
		data2[1025,1] = 0

		self.assertReportEqual(data1, data2, [
			"Value missmatch at channel 1, maximum difference of 0.225822 at sample 1025",
			])

	def test_comparewaves_missingNaN(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data1[50,1] = np.NaN

		self.assertReportEqual(data1, data2, [
			"Nan missmatch at channel 1, first at sample 50",
			])

	def test_comparewaves_expectedNaN(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data1[50,1] = np.NaN
		data2[50,1] = np.NaN

		self.assertReportEqual(data1, data2, [
			])

	def test_comparewaves_unexpectedNaN(self) :
		# TODO: Should the missingNaN and unexpectedNaN have different messages?
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data2[50,1] = np.NaN

		self.assertReportEqual(data1, data2, [
			"Nan missmatch at channel 1, first at sample 50",
			])

	def test_comparewaves_missingNaNNextHops(self) :
		data1 = self.stereoSinusoids(samples=2000)
		data2 = data1.copy()
		data1[1025,1] = np.NaN

		self.assertReportEqual(data1, data2, [
			"Nan missmatch at channel 1, first at sample 1025",
			])

	def test_comparewaves_expectedPosInf(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data1[50,1] = np.inf
		data2[50,1] = np.inf

		self.assertReportEqual(data1, data2, [])

	def test_comparewaves_missingPosInf(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data1[50,1] = np.inf

		self.assertReportEqual(data1, data2, [
			"Positive infinite missmatch at channel 1, first at sample 50",
			])

	def test_comparewaves_unexpectedPosInf(self) :
		# TODO: Should the missingPostInf and unexpectedPosInf have different messages?
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data2[50,1] = np.inf

		self.assertReportEqual(data1, data2, [
			"Positive infinite missmatch at channel 1, first at sample 50",
			])

	def test_comparewaves_expectedNegInf(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data1[50,1] = -np.inf
		data2[50,1] = -np.inf

		self.assertReportEqual(data1, data2, [])

	def test_comparewaves_missingNegInf(self) :
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data1[50,1] = -np.inf

		self.assertReportEqual(data1, data2, [
			"Negative infinite missmatch at channel 1, first at sample 50",
			])

	def test_comparewaves_unexpectedNegInf(self) :
		# TODO: Should the missingNegtInf and unexpectedNegInf have different messages?
		data1 = self.stereoSinusoids()
		data2 = data1.copy()
		data2[50,1] = -np.inf

		self.assertReportEqual(data1, data2, [
			"Negative infinite missmatch at channel 1, first at sample 50",
			])


if __name__ == '__main__' :
	import sys
	sys.exit(unittest.main())



