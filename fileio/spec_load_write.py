import pickle
from csv import DictReader, DictWriter

from common.constants import BINNED_SPEC_PATH, REST_SPEC_PATH, os
from fileio.utils import dirCheck, extCheck, fileCheck, fns, join, ns2f
from spectrum import Spectrum


def text_load( path, filename ):
    if not fileCheck( path, filename ):
        raise IOError( f"text_load: File not found{os.linesep}path: {path + os.linesep}filename: {filename}" )

    with open( join( path, filename ), 'r' ) as infile:
        """ Read header.

        File format:
            namestring=55555-4444-333,z=float(),gmag=float()
            wavelength,flux density,error

        Parse the first line, use the second as CSV reader input
         """
        header = infile.readline().strip().split( ',' )
        namestring = fns( header[ 0 ] )
        z = float( header[ 1 ].strip( "z=" ) )
        gmag = float( header[ 2 ].strip( "gmag=" ) )

        reader = DictReader( infile, fieldnames=infile.readline().strip().split( ',' ) )
        wls = []
        flux = []
        err = []
        for row in reader:
            try:
                wls.append( int( row[ 'wavelength'] ) )
            except ValueError:
                wls.append( float( row[ 'wavelength' ] ) )
            flux.append( float( row[ 'flux density' ] ) )
            err.append( float( row[ 'error' ] ) )
    spec = Spectrum( namestring = namestring, z = z, gmag = gmag )
    spec.setDict( wls, flux, err )
    return spec

def text_write( spec, path, filename ):
    """
    Writes an ASCII formatted spec file with appropriate header information.

    Format can be read in by spec_load_write.text_load() method


    :param spec: spectrum to be written
    :param path: /path/to/write/
    :param filename: filename to write in path
    :type spec: Spectrum
    :type path: str
    :type filename: str
    :return: None
    :rtype: None
    """
    dirCheck( path )

    with open( join( path, filename ), 'w' ) as outfile:
        header = "namestring=%s,z=%f,gmag=%f%s" % ( spec.getNS(), spec.getRS(), spec.getGmag(), os.linesep )
        outfile.writelines( [ header, "wavelength,flux density,error%s" % os.linesep ])

        fieldnames = [ "wavelength", "flux density", "error"]
        writer = DictWriter( outfile, fieldnames= fieldnames)
        writer.writeheader()
        writer.writerows( spec.lineDictList() )

def write( spec, path, filename ):
    """
    Writes a serialized spectrum file at /path/filename
    :param spec: spectrum to the written
    :param path: /path/to/filename
    :param filename: file name to be written to
    :type spec: Spectrum
    :type path: str
    :type filename: str
    :return: None
    """
    dirCheck( path )
    with open( join( path, filename ), 'wb' ) as outfile:
        pickle.dump( spec, outfile, protocol=pickle.HIGHEST_PROTOCOL )

def load( path, filename ):
    """
    Loads the serialized spectrum file at /path/filename

    :param path: /path/to/filename
    :param filename:  file name of spectrum to load
    :type path: str
    :type filename: str
    :rtype: Spectrum
    """
    fileCheck( path, filename )
    return pickle.load( open( join( path, filename ), 'rb' ) )

def rspecLoader( namestring ):
    return load( REST_SPEC_PATH, ns2f( namestring, ".rspec") )

def bspecLoader( namestring ):
    return load( BINNED_SPEC_PATH, ns2f( namestring, ".bspec") )

def async_load( path, filelist, extention = None ):
    """
    Uses asyncio to load serialized Spectrum from filelist ( list in [ str() ] form )

    If extension is specified, each filename in filelist will be concactated with it.  Elsewise, ignored.

    :param path: /path/to/directory
    :param filelist: filenames of spectra to be loaded
    :param extention: (optional) file extention to append to each filename before loading
    :type path: str
    :type filelist: list
    :type extention: str
    :return: list of loaded Spectrum type
    :rtype: list
    """
    import asyncio

    async def __async_load_wrapper( path, filename ):
        return load( path, filename )

    output_list = []
    load_loop = asyncio.new_event_loop()

    if extention is not None:
        filelist = [ f + extCheck( extention ) for f in filelist ]

    try:
        load_loop.run_until_complete( __async_wrapper( [ ( path, filename ) for filename in filelist ], __async_load_wrapper, output_list  ) )
    finally:
        load_loop.close()

    return output_list

def async_write( path, speclist, extention = ".spec" ):
    """
    Uses asyncio to write a speclist to the disk.

    Will set filename from spectrum namestring.  If extention is not specificed, will default to ".spec"

    :param path: /path/to/directory
    :param speclist: list of spectrum to output
    :param extention: desired file extention
    :type path: str
    :type speclist: list
    :type extention: str
    :rtype: None
    """
    import asyncio

    async def __async_write_wrapper( path, spectrum, extention ):
        write( spectrum, path, ns2f( spectrum.getNS(), extention ) )

    write_loop = asyncio.new_event_loop()

    try:
        write_loop.run_until_complete( __async_wrapper( [ ( path, spec, extention ) for spec in speclist ], __async_write_wrapper ) )
    finally:
        write_loop.close()

async def __async_wrapper( input_values, async_function, output_values = None ):
    """
    Basic asyncronous operations wrapper.  Be aware, no order will be maintained in this process.
    i.e. the results of output_values will very likely NOT correspond to those of input_values.

    input_values is a list of tuples. These values will be unpacked and passed to specified async_function

    Note:  No results are returned directly by this method.  Returned results of async_function are appended to output_values.
    If output_values is not given, no results will be returned from this method.

    :param input_values: list of tuples [ (val1, val2...), ... ] to be passed to async_function by async_function( *(val1, val2...) )
    :param async_function: asyncronous method which contains the actual operation to be performed.
    :param output_values: If passed in, results returned by async_function will be appended to this list.
    :type input_values: list
    :type async_function: function
    :type output_values: list
    :return: None
    :rtype: None
    """
    import asyncio

    coroutines = [ async_function( *input_value ) for input_value in input_values ]
    completed, pending = await asyncio.wait( coroutines )

    if output_values is not None:
        output_values.extend( [ result.result() for result in completed ] )