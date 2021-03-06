#!/usr/bin/perl

# Copyright (C) 2008-2009 Sun Microsystems, Inc. All rights reserved.
# Use is subject to license terms.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301
# USA

use strict;
use lib 'lib';
use lib '../lib';
use Carp;
use Getopt::Long;

use GenTest;
use GenTest::Properties;
use GenTest::Grammar;

my $options = {};
GetOptions(
	$options,
	'grammar=s',
	'mask=i',
	'mask-level=i'
);

my $config = GenTest::Properties->new(
	options => $options,
	defaults => {
		'mask-level'	=> 1,
		'mask'		=> 0
	},
	required => ['grammar']
);

my ($grammar_file, $mask, $mask_level) = (
	$config->property('grammar'),
	$config->property('mask'),
	$config->property('mask-level')
);

say("Grammar: $grammar_file");
say("Mask: $mask");
say("Mask-level: $mask_level");

my $initial_grammar = GenTest::Grammar->new(
	'grammar_file'	=> $grammar_file
);

my $final_grammar;

if ($mask > 0) {
	my $top_grammar = $initial_grammar->topGrammar($mask_level, "query", "query_init");
	my $masked_top = $top_grammar->mask($mask);
	$final_grammar = $initial_grammar->patch($masked_top);
} else {
	$final_grammar = $initial_grammar;
}

print $final_grammar->toString();
print "\n";
