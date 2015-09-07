from .tabulate import TableFormat, Line, DataRow


# "Vertica-bar" seperated values
vsv_unaligned = TableFormat(lineabove=None,
                            linebelowheader=None,
                            linebetweenrows=None,
                            linebelow=None,
                            headerrow=DataRow('', '|', ''),
                            datarow=DataRow('', '|', ''),
                            padding=0, with_header_hide=None)
