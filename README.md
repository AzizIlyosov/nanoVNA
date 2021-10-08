# nanoVNA
1. Reference Data Read -> Display
2. Ref boundary Display
3. nanoVNA measure data -> Display
4. Pass / Fail Determine





# function in NanoVNA-Saver
.ini -> .config/nanosaver/

## Settings/
Sweep.py


Bands.py


# UI Control function
## Controls/SweepControl.py (Setup - 2. Frequency)
    line 37 ~ 120 - UI connect 

    start, stop -> textEdited -> update_center_span() -> set span, center -> update_sweep()

    start, stop -> textChanged -> update_step_size() -> set segment -> update_sweep()

    center, span -> Use only function, Not UI
    segments -> unnecessary

    add Sweep
    add I/F bw
    add numberPad window

## NanoVNASaver.py 
### ( Setup - 1. Device connect )
    line 363 ~ 396 - serial_control
    Serial port control box => Device connect
    device ComboBox => 3 radio button ( checked nanovna )
    Connect to device button 
        serialButtonClick (toggle) (lint 520~)
            if not self.vna.connected():
                self.connect_device()
            else:
                self.disconnect_device()

        => only use connect button -> connect_device() (line 526~)

    rescan / manage -> unnecessary


                            
### ( data - 1. Call Reference )
    line 397 ~ File control
    main UI - Files ... -> Load reference

    select reference : only use default folder -> reference list -> Display Drop box 
    Set Reference Button

### ( data - 2. Save Data )
    line 397 ~ File control
    main UI - Files ... -> Export file - Save 1-Port file (S1P)

    using exportFile() - line 479


## Windows/DisplaySettings.py
### ( Setup - 3. DUT )
    Display Settings - Displayed charts
    line 339 ~
    selection = [ ] <- chart name 

    changeChart(0, 0, chart00_selection.currentText())
        - line 499

    only use two radio button
        |S11| / |S21|
    only one chart displayed


## Window/CalibrationSettings.py
### ( Setup - 4. Calibration )
    main UI - Calibration ... 








### ( data - 2. Save Data )




---------------------------------------------
# addtional function
## ( Scale / range - 1. Range Setup )
    3 button
    Max
    Min
    Auto Scale
        Auto Scale
        - If click,
            > Calculate maximum value and minimum value as
            max( abs(s-parameter) ) and min( abs(s-parameter) )
            > the range R is (maximum value – minimum value)
            > Set MAX as maximum value + R*0.1
            > Set MIN as minimum value - R*0.1

## ( Scale / range - 2. Pass Fail Range )
    3 button
    Pos. - range +5dB
    Neg. - range -5dB
    Symmetric
        - If click,
            > Neg. level is automatically changed to same value as Pos. level with with minus sign.
        ex) Pos. level 10 dB, Neg. level -5dB, press “Symmetric”, then
            > Pos. level 10 dB, Neg. level -10dB


## Continuous / Single

## Pass / Fail result

## Save / load 
### ( Setup - Save / Load )
### ( Scale / range - Save / Load )