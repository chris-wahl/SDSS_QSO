from typing import Union

from catalog import shenCat
from spectrum import Spectrum


def source_frame_step( spec: Union[ Spectrum, str ], desired_step: float = 1 ) -> float:
    """
    Determines the step size necessary in the spectrum's source frame that will yield the desired_step
    when the spectrum is shifted back to rest.

    :param spec:
    :param desired_step:
    :return:
    """
    if type( spec ) == Spectrum:
        spec = spec.getNS( )
    z = shenCat.subkey( spec, 'z' )
    return (1 + z) * desired_step


def init_source_wl( spec: Spectrum ) -> float:
    """
    When binning a source spectrum with the intention of shifting it back to rest frame and avoid re-binning,
    this method what the desired first wavelength should be in the source frame.

    Operates under the assumption that the desired rest frame bins are integer wavelength values.

    ie. if first wl in spectrum is 3805.43 at a redshift of z = 0.55, the first rest frame wavelength is 2454.4709...
    Thus, the first (integer wavelength) bin begins at 2454.

    Returning to the source frame, this becomes 3805.12.
    This method would, in this case, return 3805.12.  Pass this to the source binning process and it will begin the
    binning process there.


    :param spec: Source frame spectrum
    :type spec: Spectrum
    :return: initial source bin wavelength
    :rtype: float
    """
    z = shenCat.subkey( spec.getNS( ), 'z' )
    first_wl = spec.getWavelengths( )[ 0 ] / (1 + z)
    first_wl = int( first_wl )
    first_wl *= (1 + z)
    return first_wl


def source_bin( spec: Spectrum, step: float = None, init_wl: float = None ) -> Spectrum:
    """
    Bins a spectrum beginning given initial wavelength and desired bin spacing (step).

    Intended to be used to bin a source spectrum which will then be shifted back into rest frame (via
    binned_source_to_rest).  The rest frame spectrum will already be binned as a result.

    :param spec: Spectrum to bin
    :param step: Desired source frame bin spacing.  Will call source_frame_step( spec, 1 ) if this is not passed.
    :param init_wl: Desired inital bin wavelength.  Will call init_source_wl( spec ) if this is not passed.
    :type spec: Spectrum
    :type step: float
    :type init_wl: float
    :return: Binned source spectrum
    :rtype: Spectrum
    """
    from numpy import std, mean

    step = step or source_frame_step( spec, 1 )
    oldwls = spec.getWavelengths( )
    if init_wl is None:
        init_wl = init_source_wl( spec )

    max_wl = oldwls[ -1 ]

    newwls = [ init_wl ]

    flxlist = [ ]
    errlist = [ ]
    newi = 0
    oldi = 0

    neww = newwls[ newi ]
    oldw = oldwls[ oldi ]
    while neww + step < max_wl:  # Run until the last wavelength in spec is binned
        flux = [ ]  # clear the current range of flux values
        while oldw < neww + step:  # while the old wl is in the current bin, get its flux and advance to the next
            flux.append( spec.getFlux( oldw ) )
            oldi += 1
            oldw = oldwls[ oldi ]

        # see if the flux has more than one value (if so, take the mean and set the err as std deviation)
        # otherwise, assign it that value and error
        if len( flux ) > 1:
            err = std( flux )
            flux = float( mean( flux ) )
        elif len( flux ) == 1:
            err = spec.getErr( oldwls[ oldi - 1 ] )
            flux = flux[ 0 ]

        # if there were no values in this bin range (i.e. the flux variable is still a list, albiet an empty one)
        # then something's wrong.
        if type( flux ) == float:
            flxlist.append( flux )
            errlist.append( err )
            while neww + step < oldw:
                neww += step
            newwls.append( neww )
        else:
            print( "Well, this is awkward.  You're probably caught in an infinte loop." )
            print( f"New WL:{new}, Last old wl:{oldw} on spectrun:{spec.getNS()}" )

    spec = spec.cpy_info( )
    spec.setDict( newwls[ : -1 ], flxlist, errlist )

    return spec


def binned_source_to_rest( spec: Spectrum, z: float = None ) -> Spectrum:
    """
    Takes in a binned source spectrum and shifts it to rest frame.

    WARNING:  Assumes desired wavelengths will be integer values and called (int) on them as a result

    :param spec: Binned source spectrum
    :param z: Original redshift.  If not passed, it will call spec.getRS() and use that value.
    :type spec: Spectrum
    :type z: float
    :return: Rest frame spectrum
    :rtype: Spectrum
    """
    z = z or spec.getRS( )
    wls = spec.getWavelengths( )
    n = len( wls )
    for wl in wls:
        spec[ int( wl / (1 + z) ) ] = spec[ wl ]
        del spec[ wl ]
    return spec