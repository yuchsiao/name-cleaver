import re

DEGREE_RE = 'j\.?d\.?|m\.?d\.?|ph\.?d\.?'
SUFFIX_RE = '([js]r\.?|%s|[IVX]{2,})' % DEGREE_RE

class Name(object):
    scottish_re = r'(?i)\b(?P<mc>ma?c)(?!hin)(?P<first_letter>\w)\w+'

    def primary_name_parts(self):
        raise NotImplementedError("Subclasses of Name must implement primary_name_parts.")

    def non_empty_primary_name_parts(self):
        return ' '.join([ x for x in self.primary_name_parts() if x ])

    def is_mixed_case(self):
        return re.search(r'[A-Z][a-z]', self.non_empty_primary_name_parts())

    def uppercase_the_scots(self, name_portion):
        '''Uppercase names like MacGyver and McDonalds'''

        matches = re.search(self.scottish_re, name_portion)

        if matches:
            mc = matches.group('mc')
            first_letter = matches.group('first_letter')
            return re.sub(mc + first_letter, mc.title() + first_letter.upper(), name_portion)
        else:
            return name_portion

    def fix_case_for_possessives(self, name):
        return re.sub(r"(\w+)'S\b", "\\1's", name)


class OrganizationName(Name):
    abbreviations = {
        'acad': 'Academy',
        'assns': 'Associations',
        'assn': 'Association',
        'cmte': 'Committee',
        'cltn': 'Coalition',
        'inst': 'Institute',
        'corp': 'Corporation',
        'co': 'Company',
        'fedn' : 'Federation',
        'fed': 'Federal',
        'fzco': 'Company',
        'usa': 'USA',
        'us': 'United States',
        'dept': 'Department',
        'assoc': 'Associates',
        'natl': 'National',
        'nat\'l': 'National',
        'intl': 'International',
        'int\'l': 'International',
        'inc': 'Incorporated',
        'llc': 'LLC',
        'llp': 'LLP',
        'lp': 'LP',
        'plc': 'PLC',
        'ltd': 'Limited',
        'univ': 'University',
        'colls': 'Colleges',
        'coll': 'College',
        'amer': 'American',
        'ed': 'Educational',
        '&': 'And',
        'lc': 'Limited Company',
        'lllp': 'LLLP',
        'ltd': 'Limited',
        'pllc': 'PLLC',
        'rlllp': 'RLLLP',
        'rllp': 'RLLP',
        'svcs': 'Services',
        'ctr': 'Center',
    }
    filler_words = ['The', 'And', 'Of', 'In', 'For', 'Group', 'Unlimited']

    name = None

    #suffix = None

    def new(self, name):
        self.name = name
        return self

    def case_name_parts(self):
        if not self.is_mixed_case():
            self.name = self.name.title()
            self.name = self.uppercase_the_scots(self.name)

            if re.match(r'(?i)^\w*PAC$', self.name):
                self.name = self.name.upper() # if there's only one word that ends in PAC, make the whole thing uppercase
            else:
                self.name = re.sub(r'(?i)\bpac\b', 'PAC', self.name) # otherwise just uppercase the PAC part

            self.name = self.uppercase_the_scots(self.name)
            self.name = self.fix_case_for_possessives(self.name)

        return self

    def primary_name_parts(self):
        return [ self.without_extra_phrases() ]

    def __unicode__(self):
        return unicode(self.name)

    def __str__(self):
        return unicode(self.name).encode('utf-8')

    def without_extra_phrases(self):
        """Removes parenthethical and dashed phrases"""
        # the last parenthesis is optional, because sometimes they are truncated
        name = re.sub(r'\s*\([^)]*\)?\s*$', '', self.name)
        # remove any trailing that begins with "formerly"
        name = re.sub(r'(?i)\s* formerly.*$', '', name)
        # remove trailing " and its affiliates"
        name = re.sub(r'(?i)\s* and its affiliates$', '', name)
        # remove "et al"
        name = re.sub(r'\bet al\b', '', name)

        # in some datasets, the name of an organization is followed by a hyphen and an abbreviated name, or a specific
        # department or geographic subdivision; we want to remove this extraneous stuff without breaking names like
        # Wal-Mart or Williams-Sonoma

        # DO NOT PROCESS HYPHENATION
        # if there's a hyphen at least four characters in, proceed
        #if "-" in name:
            #hyphen_parts = name.rsplit("-", 1)
            ## if the part after the hyphen is shorter than the part before,
            ## AND isn't either a number (often occurs in Union names) or a single letter (e.g., Tech-X),
            ## AND the hyphen is preceded by either whitespace or at least four characters,
            ## discard the hyphen and whatever follows
            #if len(hyphen_parts[1]) < len(hyphen_parts[0]) \
            #        and re.search(r'^(\s+)|^(\w{0,4})$', hyphen_parts[1]) \
            #        and not re.match(r'^([a-zA-Z]|[0-9]+)$', hyphen_parts[1]):
                #name = hyphen_parts[0].strip()

        return name

    def without_punctuation(self):
        # take only the part without extra phrases()
        # ideally, it should not be here
        name = self.without_extra_phrases()

        # TODO: determine what to do with: @ % $
        # PRESERVE: ! ? + # &

        # replace '/' with a space
        name = re.sub(r'[\/=\[\]\{\}\<\>]+', ' ', name)
        # remove , . * : ; +
        name = re.sub(r'[,.*:;~^"]*', '', name)
        # normalize parathesis format from ( word... word ) to  (word... word)
        name = re.sub(r'\(\s*(.*?)\s*\)', r' (\1) ', name)
        # fix ` with '
        name = name.replace('`', "'")
        # normalize #: if followed by a number 1, then #1 instead of # 1
        name = re.sub(r'#\s+(\d+)', r'#\1', name)
        # normalize &: if both sides contain >= 2 characters, then aa & bb instead of aa&bb
        #              if not, aa&b is preferred
        name = re.sub(r'([^\s]+)\s*&\s*([^\s]+)', r'\1&\2', name)
        name = re.sub(r'([^\s]{2,})\s*&\s*([^\s]{2,})', r'\1 & \2', name)

        return name

    def expand(self):
        return ' '.join(self.abbreviations.get(w.lower(), w) for w in self.without_punctuation().split())

    def kernel(self):
        """ The 'kernel' is an attempt to get at just the most pithy words in the name """
        stop_words = [ y.lower() for y in self.abbreviations.values() + self.filler_words ]
        kernel = ' '.join([ x for x in self.expand().split() if x.lower() not in stop_words ])

        # this is a hack to get around the fact that this is the only two-word phrase we want to block
        # amongst our stop words. if we end up with more, we may need a better way to do this
        # do not block if name begins with United States, e.g., United States Postal Services
        kernel = re.sub(r'\s+United States', '', kernel)

        return kernel

    def crp_style_firm_name(self, with_et_al=True):
        if with_et_al:
            return ', '.join(self.kernel().split()[0:2] + ['et al'])
        else:
            return ', '.join(self.kernel().split()[0:2])


class PersonName(Name):
    honorific = None
    first = None
    middle = None
    last = None
    suffix = None
    nick = None

    family_name_prefixes = ('de', 'di', 'du', 'la', 'van', 'von')
    allowed_honorifics = ['mrs', 'mrs.']

    def new(self, first, last, **kwargs):
        self.first = first.strip()
        self.last = last.strip()

        self.set_and_clean_option('middle', kwargs)
        self.set_and_clean_option('suffix', kwargs)
        self.set_and_clean_option('honorific', kwargs)
        self.set_and_clean_option('nick', kwargs)

        return self

    def set_and_clean_option(self, optname, kwargs):
        optval = kwargs.get(optname)

        if optval:
            optval = optval.strip()
            setattr(self, optname, optval)

    def new_from_tokens(self, *args, **kwargs):
        """
            Takes in a name that has been split by spaces.
            Names which are in [last, first] format need to be preprocessed.
            The nickname must be in double quotes to be recognized as such.

            This can take name parts in in these orders:
            first, middle, last, nick, suffix, honorific
            first, middle, last, nick, suffix
            first, middle, last, suffix, honorific
            first, middle, last, honorific
            first, middle, last, suffix
            first, middle, last, nick
            first, last, honorific
            first, last, suffix
            first, last, nick
            first, middle, last
            first, last
            last
        """

        if kwargs.get('allow_quoted_nicknames'):
            args = [ x.strip() for x in args if not re.match(r'^[(]', x) ]
        else:
            args = [ x.strip() for x in args if not re.match(r'^[("]', x) ]

        if len(args) > 2:
            self.detect_and_fix_two_part_surname(args)

        # set defaults
        self.first = ''
        self.last = ''

        # the final few tokens should always be detectable, otherwise a last name
        if len(args):
            if self.is_an_honorific(args[-1]):
                self.honorific = args.pop()
                if not self.honorific[-1] == '.':
                    self.honorific += '.'
            if self.is_a_suffix(args[-1]):
                self.suffix = args.pop()
                if re.match(r'[js]r(?!\.)', self.suffix, re.IGNORECASE):
                    self.suffix += '.'
            if self.is_a_nickname(args[-1]):
                self.nick = args.pop()
            self.last = args.pop()

        num_remaining_parts = len(args)

        if num_remaining_parts == 3:
            # if we've still got this many parts, we'll consider what's left as first name
            # plus multi-part middle name
            self.first = args[0]
            self.middle = ' '.join(args[1:3])

        elif num_remaining_parts == 2:
            self.first, self.middle = args
            if len(self.middle) == 1:
                self.middle += '.'

        elif num_remaining_parts == 1:
            self.first = ' '.join(args)

        if self.first and len(self.first) == 1:
            self.first += '.'

        return self

    def is_a_suffix(self, name_part):
        return re.match(r'^%s$' % SUFFIX_RE, name_part, re.IGNORECASE)

    def is_an_honorific(self, name_part):
        return re.match(r'^\s*[dm][rs]s?[.,]?\s*$', name_part, re.IGNORECASE)

    def is_a_nickname(self, name_part):
        """
        Nicknames, in our data, often come wrapped in parentheses or the like. This detects those.
        """
        return re.match(r'^["(].*[")]$', name_part)

    def detect_and_fix_two_part_surname(self, args):
        """
        This detects common family name prefixes and joins them to the last name,
        so names like "De Kuyper" don't end up with "De" as a middle name.
        """
        i = 0
        while i < len(args) - 1:
            if args[i].lower() in self.family_name_prefixes:
                args[i] = ' '.join(args[i:i+2])
                del(args[i+1])
                break
            else:
                i += 1

    def __unicode__(self):
        return unicode(self.name_str())

    def __str__(self):
        return unicode(self.name_str()).encode('utf-8')

    def name_str(self):
        return ' '.join([x.strip() for x in [
            self.honorific if self.honorific and self.honorific.lower() in self.allowed_honorifics else None,
            self.first,
            self.middle,
            self.nick,
            self.last + (',' if self.suffix else ''),
            self.suffix
        ] if x])

    def case_name_parts(self):
        """
        Convert all the parts of the name to the proper case... carefully!
        """
        if not self.is_mixed_case():
            self.honorific = self.honorific.title() if self.honorific else None
            self.nick = self.nick.title() if self.nick else None

            if self.first:
                self.first = self.first.title()
                self.first = self.capitalize_and_punctuate_initials(self.first)

            if self.last:
                self.last = self.last.title()
                self.last = self.uppercase_the_scots(self.last)

            self.middle = self.middle.title() if self.middle else None

            if self.suffix:
                # Title case Jr/Sr, but uppercase roman numerals
                if re.match(r'(?i).*[js]r', self.suffix):
                    self.suffix = self.suffix.title()
                else:
                    self.suffix = self.suffix.upper()

        return self

    def is_only_initials(self, name_part):
        """
        Let's assume we have a name like "B.J." if the name is two to three
        characters and consonants only.
        """
        return re.match(r'(?i)[^aeiouy]{2,3}$', name_part)

    def capitalize_and_punctuate_initials(self, name_part):
        if self.is_only_initials(name_part):
            if '.' not in name_part:
                return ''.join([ '{0}.'.format(x.upper()) for x in name_part])
            else:
                return name_part
        else:
            return name_part

    def primary_name_parts(self, include_middle=False):
        if include_middle:
            return [ self.first, self.middle, self.last ]
        else:
            return [ self.first, self.last ]

    def as_dict(self):
        return { 'first': self.first, 'middle': self.middle, 'last': self.last, 'honorific': self.honorific, 'suffix': self.suffix }

    def __repr__(self):
        return self.as_dict()


class PoliticalMetadata(object):
    party = None
    state = None

    def plus_metadata(self, party, state):
        self.party = party
        self.state = state

        return self

    def __str__(self):
        if self.party or self.state:
            party_state = u"-".join([ x for x in [self.party, self.state] if x ]) # because presidential candidates are listed without a state
            return unicode(u"{0} ({1})".format(unicode(self.name_str()), party_state)).encode('utf-8')
        else:
            return unicode(self.name_str()).encode('utf-8')


class PoliticianName(PoliticalMetadata, PersonName):
    pass


class RunningMatesNames(PoliticalMetadata):

    def __init__(self, mate1, mate2):
        self.mate1 = mate1
        self.mate2 = mate2

    def name_str(self):
        return u' & '.join([unicode(self.mate1), unicode(self.mate2)])

    def __repr__(self):
        return self.__str__()

    def mates(self):
        return [ self.mate1, self.mate2 ]

    def is_mixed_case(self):
        for mate in self.mates():
            if mate.is_mixed_case():
                return True

        return False

    def case_name_parts(self):
        for mate in self.mates():
            mate.case_name_parts()

        return self


