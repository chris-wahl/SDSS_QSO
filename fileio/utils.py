from re import search
from typing import List, Union

from common.constants import abspath, join, os


def dirCheck( *args : Union[ list or str ] ) -> None:
    """
    Checks if a given path exists.  If not, creates the folders to it.

    join( *args ) will be called on all passed parameters before checking

    :param args: string list of /path/to/dir
    :type args: list or str
    :return: None
    :rtype: None
    """
    path = join( *args )
    if not os.path.isdir( path ):
        os.makedirs( path )


def extCheck( extention: str ) -> str:
    """
    Ensures a file extention includes the leading '.'

    :param extention: file extention
    :type extention: str
    :return: Properly formatted file extention
    :rtype: str
    """
    if extention[ 0 ] != '.':
        extention = '.' + extention
    return extention


def fileCheck( path: str, filename: str = "" ) -> None:
    """
    Checks if a file exists.  If not, raises FileNotFound error

    Note, if filename is not passed, it will default to "" and only the
    value of path is checked.  Thus, if path does not hold a file, the exception will be raised.
    This is NOT a folder check.  Use dirCheck() for checking/creating a folder.

    :param path: /path/to/file
    :param filename: file.name
    :type path: str
    :type filename: str
    :rtype: None
    """
    if not os.path.isfile( abspath( join( path, filename ) ) ):
        raise FileNotFoundError( f"{join( path, filename )}" )


def findNamestring( inputString: str ) -> str:
    """
    Uses regular expressions to find MJD-Plate-Fiber string.

    If none is found, raises a ValueError

    :param inputString: given string containing a namestring
    :type inputString: str
    :rtype: str
    :return: First instance of namestring format
    :raises: ValueError
    """
    try:
        return search( r'\d{5}-\d{4}-\d{3}', inputString ).group( 0 )
    except:
        raise ValueError( "Unable to find namestring in the given inputString.\ninputString: %s" % inputString )


def fns( inputString: str ) -> str:
    """
    Shortcut call to utils.findNamestring( inputString )

    :param inputString: String to be seached for namestring format
    :type inputString: str
    :return: Namestring
    :rtype: str
    """
    return findNamestring( inputString )


def getFiles( path: str, extention: str = None ) -> List[ str ]:
    """
    Returns a list of all files within the given path.

    If extention is specified, will only return files with said extention

    :param path: /path/to/directory/of/interest
    :param extention: File extention of interest.  If not specified, all files in directory are returned
    :type path: str
    :type extention: str
    :return: List of str() files in directory.  If extention is specified, only those files with that file extention are returned.
            Note that this list will NOT include the /path/to/ in the file names - merely the names themselves
    :rtype: list
    """
    extention = extCheck ( extention ) if extention is not None else ''
    return[ f for f in os.listdir( path ) if ( os.path.isfile( os.path.join( path, f ) ) and (os.path.splitext( f )[ 1 ].endswith( extention ))) ]


def object_loader( path: str, filename: str ) -> object:
    import pickle
    fileCheck( path, filename )
    return pickle.load( open( join( path, filename ), 'rb' ) )


def object_writer( object: object, path: str, filename: str ) -> None:
    import pickle
    dirCheck( path )
    with open( join( path, filename ), 'wb' ) as outfile:
        pickle.dump( object, outfile, protocol=pickle.HIGHEST_PROTOCOL )


def ns2f( namestring: str, extention: str ) -> str:
    """
    Shortcut call for utils.namestringToFilename( namestring, extention )

    :param namestring: leading filename
    :param extention:  file extention
    :type namestring: str
    :type str
    :return: concatated filename
    :rtype str
    """
    return namestringToFilename( namestring, extention )


def namestringToFilename( namestring: str, extention: str ) -> str:
    """
    Concatates namestring & extention, passing extention through extCheck first

    :param namestring: leading filename
    :param extention:  file extention
    :type namestring: str
    :type str
    :return: concatated filename
    :rtype str
    """
    return namestring + extCheck( extention )