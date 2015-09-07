from .tabulate import TableFormat, Line, DataRow


# "Vertica-bar" seperated values
vsv_aligned = TableFormat(lineabove=None,
                          linebelowheader=Line('', '-', '+', ''),
                          linebetweenrows=None,
                          linebelow=None,
                          headerrow=DataRow('', '|', ''),
                          datarow=DataRow('', '|', ''),
                          padding=1, with_header_hide=None)

vsv_unaligned = TableFormat(lineabove=None,
                            linebelowheader=None,
                            linebetweenrows=None,
                            linebelow=None,
                            headerrow=DataRow('', '|', ''),
                            datarow=DataRow('', '|', ''),
                            padding=0, with_header_hide=None)
