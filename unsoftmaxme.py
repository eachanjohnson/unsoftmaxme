#!/usr/bin/env python

__author__ = 'Eachan Johnson'

__doc__ = '''
Usage:  unsoftmaxme.py (--help | --version)
        unsoftmaxme.py -o <output> <files>...

Options:
--help, -h                          Show this message and exit
--version                           Show version number and exit
-o <output>, --output <output>      Filename to use for output
<files>...                          Data files from SoftMax in CSV format
'''

import csv
import docopt
import string

# define classes


class Table(object):

    def __init__(self):
        self.headers = None
        self.data = {}
        self.dimensions = (0, 0)

    def add_headers(self, headers):

        if self.headers is None:
            self.headers = {header: n for n, header in enumerate(headers)}
            self.data = {header: [] for header in self.headers}
        else:
            raise AttributeError('Headers are immutable')

        return self

    def add_row(self, row):

        for header in self.data:
            row_index_for_this_header = self.headers[header]
            self.data[header].append(row[row_index_for_this_header])

        number_of_rows = len(self.data[list(self.headers)[0]])
        number_of_columns = len(list(self.headers))

        self.dimensions = (number_of_rows, number_of_columns)

        return self

    def from_plate_matrix(self, plate):

        table_headers = list(self.data)
        data_table = {header: [] for header in table_headers}

        for row in plate.row_data:
            row_number = _letter_to_number(row)

            for column_index, datum in enumerate(plate.row_data[row]):
                column_number = int(column_index) + 1
                data_table['row'].append(row)
                data_table['row_number'].append(row_number)
                data_table['column'].append(column_number)
                data_table['value'].append(datum)

        data_table['filename'] = [plate.source_filename for _ in range(len(data_table['row']))]
        data_table['plate_name'] = [plate.name for _ in range(len(data_table['row']))]
        data_table['temperature'] = [plate.temperature for _ in range(len(data_table['row']))]
        data_table['measurement_type'] = [plate.measurement_type for _ in range(len(data_table['row']))]

        self.data = data_table

        return self

    def append(self, table):

        if self.headers is None:
            self.add_headers(table.headers)

        missing_headers = []

        for header in self.data:
            try:
                #print header, table.data[header]
                self.data[header] += table.data[header]
            except KeyError as e:
                extra_headers.append(e)

        if len(missing_headers) > 0:
            raise KeyError('Data to append has extra headers: {}'.format(', '.join(missing_headers)))

        extra_headers = list(set(table.data) - set(self.data))
        if len(extra_headers) > 0:
            print 'Warning: ignoring extra headers in data to append: {}'.format(', '.join(extra_headers))

        return self

    def to_csv(self, filename):

        with open(filename, 'w') as f:
            c = csv.writer(f)
            c.writerow([header for header in self.data])
            for n, _ in enumerate(self.data[list(self.headers)[0]]):
                c.writerow([self.data[header][n] for header in self.data])

        return self

    def __getitem__(self, item):

        return self.data[item]


    def __str__(self):

        string_to_return = 'Table with {} rows and {} columns\n\n'.format(self.dimensions[0], self.dimensions[1])

        header_line = '\t'.join(list(self.data))

        inter_item_whitespace = {header: ' ' * (len(header) + 8 - 1) for header in self.data}

        string_to_return += header_line

        separator_line = '\n' + '_' * len(header_line) + '_' * 7 * header_line.count('\t')

        string_to_return += separator_line

        if self.dimensions[0] < 5:
            number_of_rows_to_print = self.dimensions[0]
        else:
            number_of_rows_to_print = 5

        for row_number in range(number_of_rows_to_print):
            string_to_return += '\n'
            string_to_return += ''.join(['{}{}'.format(self.data[header][row_number], inter_item_whitespace[header])
                                         for header in self.data])

        string_to_return += separator_line

        return string_to_return


class Configuration(object):

    def __init__(self):
        self.filename = None
        self.table = Table()

    def from_csv(self, filename):

        self.filename = filename

        with open(filename, 'rU') as f:
            c = csv.reader(f)
            for n, row in enumerate(c):
                if n > 0:
                    self.table.add_row(row)
                else:
                    self.table.add_headers(row)

        return self

    def __str__(self):

        string_to_return = str(self.table)

        return string_to_return


class Plate(object):

    def __init__(self, name, source_filename, measurement_type, temperature):
        self.name = name
        self.measurement_type = measurement_type
        self.temperature = temperature
        self.source_filename = source_filename
        self.dimensions = (None, None)
        self.number_of_wells = None
        self.row_names = {}
        self.column_names = {}
        self.row_data = {}
        table_headers = ['filename', 'plate_name', 'measurement_type',
                         'temperature', 'row', 'row_number', 'column', 'value']
        self.data_table = Table().add_headers(table_headers)

    def _refresh(self):

        self.dimensions = len(self.row_names), len(self.column_names)
        self.number_of_wells = self.dimensions[0] * self.dimensions[1]
        self.data_table.from_plate_matrix(self)

        return self

    def new_row(self, row, location):

        if len(self.column_names) == 0:
            self.column_names = {n: n for n in range(0, len(row) + 1)}

        self.row_names[location] = _letter_to_number(location)
        self.row_data[location] = [float(value) for value in row]
        self._refresh()

        return self

    def append_row(self, row):

        try:
            last_row_number = max([self.row_names[row_letter] for row_letter in self.row_names])
        except ValueError:
            last_row_number = 0
        self.new_row(row, string.letters[last_row_number].upper())

        return self

    def __str__(self):

        string_to_return = ', '.join([self.source_filename, self.name, str(self.number_of_wells)])

        return string_to_return


class SoftmaxData(object):

    def __init__(self):
        self.filename = None
        self.plates = []

    def from_csv(self, filename, plate_start='Plate:', plate_end='~End'):

        self.filename = filename

        with open(filename, 'rU') as f:
            c = csv.reader(f)
            in_plate = False
            current_plate_name = ''
            current_measurement_type = ''
            current_plate = None

            for row in c:
                try:
                    plate_flag = row[0]
                except IndexError:
                    pass
                else:
                    if plate_flag == plate_start:
                        in_plate = True
                        current_plate_name = row[1]
                        current_measurement_type = row[5]
                    elif plate_flag == plate_end:
                        self.plates.append(current_plate)
                        in_plate = False

                    if in_plate and len(list(set(row))) > 1:

                        #print row

                        if 'Temperature' in row[1]:
                            current_row_names = [int(item) for item in row if '{}'.format(item).isdigit()]
                            #print current_row_names
                            current_row_length = max(current_row_names)
                            current_row_end_index = current_row_length + 1
                        elif row[1] != '' and row[1][0].isdigit():
                            current_temperature = row[1]
                            current_plate = Plate(current_plate_name, self.filename,
                                                  current_measurement_type, current_temperature)
                            current_plate.append_row(row[2:current_row_end_index])
                        elif row[0] != plate_start:
                            current_plate.append_row(row[2:current_row_end_index])

        return self

    def __str__(self):

        string_to_return = '\n'.join(['{}'.format(str(plate)) for plate in self.plates])

        return string_to_return




# define functions
def _letter_to_number(letter):

        number = string.letters.find(letter.lower()) + 1

        return number

def main():

    options = docopt.docopt(__doc__, version='0.1')  # parse options

    #config_file = options['--config']
    data_files = options['<files>']
    output_filename = options['--output']

    print 'Welcome to UnSoftMax me!'
    #print 'Config file is {}'.format(config_file)
    print 'Data files are {}'.format(', '.join(data_files))

    #config_table = Configuration().from_csv(config_file)
    #print(config_table)
    all_softmax_data = []
    all_data = Table()

    for data_file in data_files:
        print 'Processing {}'.format(data_file)
        softmax_data = SoftmaxData().from_csv(data_file)
        all_softmax_data.append(softmax_data)
        for plate in softmax_data.plates:
            #print plate
            try:
                all_data.append(plate.data_table)
            except AttributeError:
                pass

    print 'Writing tidy data to {}'.format(output_filename)
    all_data.to_csv(output_filename)

    print 'Done!'

    return None

# boilerplate
if __name__ == '__main__':
    main()