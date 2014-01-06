#!/usr/bin/python

import os
import sys
import difflib

from docstring import DocString
from pmtools import get_files_from_dir


class PyComment(object):
    '''This class allow to manage several python scripts docstrings.
    It is used to parse and rewrite in a Pythonic way all the functions, methods and classes docstrings.

    '''
    def __init__(self, input_file, output_prefix='pyment_', doc_type='normal', param_type='standard'):
        '''Set the configuration including the source to proceed and options.

        @param input_file: path name (file or folder)
        @param output_prefix: if given will be added at the beginning of each file so it will not modify the original. 
        If None the original file will be updated. By default will add "pyment_"
        @param doc_type: the type of doctrings format. Can be:
            - normal:
                Comment on the first line, a blank line to separate the params and a blank line at the end
                e.g.: def method(test):
                        >"""The comment for this method.
                        >
                        >@param test: the param test comment
                        >@return: the result of the method
                        >
                        >"""
        @param param_type: the type of parameters format. Can be:
            - standard:
                The style used is the javadoc style.
                e.g.: @param my_param: the description
        @param recursive: In case of a folder, will proceed the subdirectories files also

        '''
        self.file_type = '.py'
        self.filename_list = []
        self.input_file = input_file
        self.output_prefix = output_prefix
        self.doc_type = doc_type
        self.param_type = param_type
        self.fd = None
        self.doc_index = -1
        self.file_index = 0
        self.docs_list = []
        self.parsed = False

        self._open_file()

    def _open_file(self):
        '''Set the new current file to proceed.

        @return: the new current file name. None if there is no more file to proceed.

        '''
        try:
            self.fd = open(self.input_file)
        except:
            msg = BaseException('Failed to open file "' + self.input_file + '". Please provide a valid file.')
            raise msg

    def _get_next(self):
        '''Get the current file's next docstring

        '''

    def _parse(self):
        '''Parses the input file's content and generates a list of its elements/docstrings.

        '''
        if self.fd is None:
            raise 'There is no current file opened to explore the elements.'
        #TODO manage decorators
        #TODO manage default params with strings escaping chars as (, ), ', ', #, ...
        #TODO manage multilines
        elem_list = []
        reading_element = False
        reading_docs = None
        waiting_docs = False
        raw = ''
        start = 0
        end = 0
        for i, ln in enumerate(self.fd.readlines()):
            l = ln.strip()
            if l.startswith('def ') or l.startswith('class '):
                # if currently reading an element content
                if reading_element:
                    if reading_docs is not None:
                        #FIXME there is a pb
                        raise 'reach new element before end of docstring'
                reading_element = True
                waiting_docs = True
                e = DocString(l)
                elem_list.append({'docs':e, 'location': (-i, -i)})
            else:
                if waiting_docs and ('"""' in l or "'''" in l):
                    # start of docstring bloc
                    if not reading_docs:
                        start = i
                        # determine which delimiter
                        idx_c = l.find('"""')
                        idx_dc = l.find("'''")
                        lim = '"""'
                        if idx_c >= 0 and idx_dc >= 0:
                            if idx_c < idx_dc:
                                lim = '"""'
                            else:
                                lim = "'''"
                        elif idx_c < 0:
                            lim = "'''"
                        reading_docs = lim
                        raw = ln
                        # one line docstring
                        if l.count(lim) == 2:
                            end = i
                            elem_list[-1]['docs'].parse_docs(raw)
                            elem_list[-1]['location'] = (start, end)
                            reading_docs = None
                            waiting_docs = False
                            reading_element = False
                            raw = ''
                    # end of docstring bloc
                    elif waiting_docs and lim in l:
                        end = i
                        raw += ln
                        elem_list[-1]['docs'].parse_docs(raw)
                        elem_list[-1]['location'] = (start, end)
                        reading_docs = None
                        waiting_docs = False
                        reading_element = False
                        raw = ''
                    # inside a docstring bloc
                    elif waiting_docs:
                        raw += ln
                # no docstring found for current element
                elif waiting_docs and l != '' and reading_docs is None:
                    waiting_docs = False
                else:
                    if reading_docs is not None:
                        raw += ln
        self.docs_list = elem_list
        self.parsed = True
        return elem_list

    def diff(self, which=-1):
        '''Build the diff between original docstring and proposed docstring.

        @param which: indicates which docstring to proceed:
        -> -1 means all the dosctrings of the file
        -> >=0 means the index of the docstring to proceed
        @return: the resulted diff
        @rtype: string

        '''
        if not self.parsed:
            self.parse()
        if self.fd is None:
            raise 'There is no current file opened to do a diff.'
        self.fd.seek(0)
        list_from = self.fd.readlines()
        list_to = []
        last = 0
        for e in self.docs_list:
            start, end = e['location']
            if start < 0:
                list_to.extend(list_from[last:-start + 1])
            else:
                list_to.extend(list_from[last:start])
            docs = e['docs'].get_raw_docs()
            list_docs = [l + '\n' for l in docs.split('\n')]
            list_to.extend(list_docs)
            last = end + 1
        if last < len(list_from):
            list_to.extend(list_from[last:])
        fromfile = 'a/' + os.path.basename(self.input_file)
        tofile = 'b/' + os.path.basename(self.input_file)
        diff_list = difflib.unified_diff(list_from, list_to, fromfile, tofile)
        return [d for d in diff_list]

    def diff_to_file(self, patch_file):
        '''
        '''
        diff = self.diff()
        f = open(patch_file, 'w')
        f.writelines(diff)
        f.close()

    def proceed(self):
        '''
        '''
        self._parse()
        for e in self.docs_list:
            e['docs'].generate_docs()
        return self.docs_list

    def release(self):
        '''Close the current file if any.'''
        try:
            self.fd.close()
        except:
            pass

    def test(self, bob):
        print 'nothing'
        var = bob
        '''affecting bob'''


if __name__ == "__main__":
    source = sys.argv[0]

    if len(sys.argv) > 1:
        source = sys.argv[1]

    files = get_files_from_dir(source)

    for f in files:
        c = PyComment(f)
        c.proceed()
        c.diff_to_file(os.path.basename(f)+".patch")
        c.release()