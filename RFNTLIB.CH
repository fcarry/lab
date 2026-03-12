/***
*	RFntLib.ch
*
*	Header file for the Clipper Library RFntLib v1.0
*
*	Copyright (c) 1994  Rolf van Gelder, All rights reserved
*
*	Date: 02/01/94
*/

*==========================================================================
* Return codes for RFntLib functions
*==========================================================================

#define	FL_OKAY			0	&& No errors detected
#define	FL_INVALID_PARMS	1	&& Invalid parameter(s) passed
#define	FL_ALLOCATE_MEMORY	2	&& Not enough memory
#define	FL_ERROR_OPENING	3	&& Error opening font file
#define	FL_ERROR_READING	4	&& Error reading font file

*==========================================================================
* Array with pre-defined error messages
*==========================================================================

#define	FL_ERRMSG	{ 'Invalid parameter(s) passed', ;
			  'Not enough memory', ;
			  'Error OPENING font file',;
                          'Error READING font file' }


*==========================================================================
* Constants
*==========================================================================

#define	FL_EGAFONTSIZE		3584	&& Size of an EGA font file
#define	FL_VGAFONTSIZE		4096	&& Size of a  VGA font file

#define	FL_EGALINES		14	&& Number of scanlines EGA font
#define	FL_VGALINES		16	&& Number of scanlines VGA font


*==========================================================================
* Icons/Symbols in the RSymbol1 and RSymbol2 Fonts (EGA & VGA)
*==========================================================================

*-- Left & Right Arrows
#define	FL_LeftArr1	'µ'		&& Chr (181)
#define	FL_RightArr1	'∂'		&& Chr (182)

*-- Floppy disk drive icon
#define	FL_DiskDrv	'∆«'		&& Chr (198) + Chr (199)

*-- Document/File Icon
#define	FL_Document	' À'		&& Chr (202) + Chr (203)

*-- Directory Icon
#define	FL_Directory	'œ–'		&& Chr (207) + Chr (208)

*-- Executable File Icon
#define	FL_EXE		'—“'		&& Chr (109) + Chr (210)

*-- Floppy Disk Icon
#define	FL_Floppy	'”‘'		&& Chr (211) + Chr (212)

*-- Big Left & Right Arrows
#define	FL_BigLeftArr	'’÷'		&& Chr (213) + Chr (214)
#define	FL_BigRightArr	'◊ÿ'		&& Chr (215) + Chr (216)

*-- Copywrite Sign
#define	FL_Copywrite	'‡'		&& Chr (224)

*-- Return Key Symbol
#define	FL_Return	'·'		&& Chr (225)

*-- Telephone Symbol
#define	FL_Phone		'‚'		&& Chr (226)

*-- Function Keys
#define	FL_F1		'„'		&& Chr (227)
#define	FL_F2		'‰'		&& Chr (228)
#define	FL_F3		'Â'		&& Chr (229)
#define	FL_F4		'Ê'		&& Chr (230)
#define	FL_F5		'Á'		&& Chr (231)
#define	FL_F6		'Ë'		&& Chr (232)
#define	FL_F7		'È'		&& Chr (233)
#define	FL_F8		'Í'		&& Chr (234)
#define	FL_F9		'Î'		&& Chr (235)
#define	FL_F10		'Ï'		&& Chr (236)

*-- Hourglass
#define	FL_Hourglass	'Ì'		&& Chr ( 237 )

*-- Left & Right Arrows
#define	FL_LeftArr2	'Ó'		&& Chr ( 238 )
#define	FL_RightArr2	'Ô'		&& Chr ( 239 )
*
* Eof RFntLib.CH