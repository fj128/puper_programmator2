;E10MA00.ASM  E10 - version EPROM  MA - PANEL MAGELAN 00 SUBVERSION FOR mAGELAN
;MEMORY MAP
;06.08.2000  message groups changed to 8 in filter
;-------------------------------;
;   PN       J   U    M     P   E  R  = PN #3
;   D7 |  D6 | D5 | D4 | D3 | D2 | D1 | D0 |
;
; Back1 Back0 Ip1  Ip0  =  1  ;if IP1 = 1 -> reserve IP adress available
;
;PANEL tYPE: PUSHBUTON  0x00  DALLAS   0x01  Ademco 02 Magelan 03 Kodinis 4
     ORG     0000h       ; 38h,
;            AA   AA  TY  PN   HH      MM   KK  KK   PP   UU   U0
        DB   12h, 34h, 0, 13h, 02h,   058H, 16h,02h, 00h, 00h, 00h


;-------------------------------;
;D7      |D6  |  D5  | D4   || D.3  | D.2     | D.1 |D.0
;1=Active|MESS|1=PGM2|1=PGM1||   x  | 1=24H   |     |0=NO
;
;        Th, Tl, Td     DD   0K_KK     0K_KK  PP     0U_UU
;                                       Alarm    Recovery
;                                       arm      disarm
      ORG 12                       ;    close    open
        DB       0, 0,10 , 11000100B, 11H,30H, 31H, 30H, 00H, 00H, 00H   ;PIN1
        DB 0 ;CLS
      ORG 24
        DB       0, 0,120 , 10000100B, 11H,20H, 31H, 20H, 01H, 00H, 00H   ;PIN2
        DB 0;CLS
      ORG 036
        DB       0,10,10 , 10000100B, 11H,20H, 31H, 20H, 02H, 00H, 00H   ;PIN3
        DB 0 ;CLS
      ORG 48
        DB       0, 0,10 , 10000100B, 11H,10H, 31H, 10H, 00H, 00H, 00H   ;PIN4
        DB 0
      ORG 60
        DB       0, 0,10 , 10000100B, 16H,11H, 16H, 11H, 00H, 00H, 00H   ;PIN5
        DB 0 ;CLS
      ORG 72
        DB       0, 0,10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 10H   ;PIN6
        DB 0 ;CLS
      ORG 84
        DB      60,60,10 , 10000100B, 13H,01H, 33H, 01H, 00H, 00H, 00H   ;PIN7
        DB 0;CLS
      ORG 96
        DB       0, 0,120 , 10000100B, 11H,44H, 31H, 44H, 00H, 00H, 00H   ;PIN8
        DB 0 ;CLS
      ORG 108
        DB      2, 0,10 , 11010000B, 14H,00H, 34H, 00H, 00H, 00H, 00H   ;PIN9  ARM
        DB 0 ;CLS
      ORG 120
        DB      0,21,120 , 10000101B, 13H,02H, 33H, 02H, 00H, 00H, 00H   ;Pbat
        DB 0 ;CLS
; PGM1 PGM2
; TA arm/disarm 0.05 sek | TI pulse 0..20 x 0.05 sek 20..255 x 1 sek
; pin9 ON(ARm),  pin9 OFF(Disarm),  pinx ON , pinx OFF,
; DD     D.7 0 - notused,1-used|D.6 - 0| D.5 - 1=user|D.4 - 1=pin
;        D.3 - 0| D.2 - 0 |D.1 0-potential, 1-pulse| D.0(0=NO,1=NC)
     ORG     00132  ;5
        DB       5, 5, 30, 0, 10110011B        ;PGM1
     ORG     00137  ;5
        DB       10, 5, 40, 30, 10110001B       ;PGM2
;
    ORG 0142   ;16
    DB   '159.148.46.210',0,0,0h,0FFh              ; ip1 0FFh =cls 18
;    DB   '195.13.239.000',0,0,0h,0FFh              ; ip1 0FFh =cls 18
    ORG  158   ;5
    DB   '3216', 0,                              ; PORT1 0FFh =cls 8
    ORG 0163    ;20
    DB   'internet.lmt.lv', 0, 0           ; Point1  0FFh =cls 14
    ;
    ORG 0183    ;16
    DB   '195.13.239.243',0,0h,0FFh              ;AP ip1 0FFh =cls 18
;    DB   '195.13.239.001',0,0h,0FFh              ;AP ip1 0FFh =cls 18
    ORG  0199    ;5
    DB   '3301', 0,0,0,0FFh                          ; PORT1 0FFh =cls 8
    ORG  0204    ;20
    DB   'internet.bite.lv', 0, 0           ; Point1  0FFh =cls 14

    ORG     0224
;16x2  Backup numbers     224. (16*2) = 32   ..255
        DB   '37129287008',0,0,0,0,0  ;   BACKUP0
        DB   '37129412743',0,0,0,0,0  ;   BACKUP1
    ORG     0256
;16x8  User numbers     256 (16*8) = 128    .. 383

        DB   '37129412743',0,0,0,0,0  ;Tel. 1
        DB   '37129287008',0,0,0,0,0  ;Tel. 2
        DB   '37111111111',0,0,0,0,0  ;Tel. 3
        DB   '37129287008',0,0,0,0,0  ;Tel. 4
        DB   '37129287008',0,0,0,0,0  ;Tel. 5
        DB   '37129287008',0,0,0,0,0  ;Tel. 6
        DB   '37129287008',0,0,0,0,0  ;Tel. 7
        DB   '37129287008',0,0,0,0,0  ;Tel. 8

       ORG     384       ;
; White tel numbers      384  (10 x 8 = 80) .. 463
; NN NN NN NN Dd  PP PP CLS
; NN NN NN NN  - 8 last digits
; Dd -Dd.3 PGM2   Dd.2 PGM1  Dd.1 Arm/disarm Dd.0 1 = PIN MAGELAN
; PP PP - Pin 4 digit
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 1
        DB   FFH, 29H, 41H, 27H, 43H, 0FH, 12H, 34H  ;Tel. 2
        DB   FFH, 29H, 28H, 70H, 08H, 0FH, 12H, 34H   ;Tel. 3
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 4
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 5
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 6
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 7
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 8
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 9
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 10

;    DB     00001111B                        ; 1 = Allowed Ip or Sim
; MESSAGE KROSS REFERENCE 464  (16 * 4 = 64)   .. 517
;       D0                         D1                        D2
; D7 D6 D5 D4 D3 D2 D1 D0 | D7 D6 D5 D4 D3 D2 D1 D0 | D7 D6 D5 D4 D3 D2 D1 D0 |
; T7 T6 T5 T4 T3 T2 T1 T0 | TF TE TD TC TB TA T9 T8 |  x  1  1    MESSAGE NR.
;                                                         |  |_ text MESSAGE
;                                                         |____ STANDART MESSAGE

  ORG 464
  ;
  DB  01H, 00H, 60H , 61H ;#1  PIN1 rec T1 MES STAND + TXT 0| Alarm
  DB  00H, 00H, 62H , 63H ;#2  PIN2
  DB  00H, 00H, 64H , 65H ;#3  PIN3
  DB  00H, 00H, 65H , 60H ;#4  PIN4
  DB  00H, 00H, 60H , 60H ;#5  PIN5
  DB  00H, 00H, 60H , 60H ;#6  PIN6
  DB  00H, 00H, 60H , 60H ;#7  PIN7
  DB  00H, 00H, 60H , 60H ;#8  PIN8
  DB  01H, 00H, 60H , 61H ;#9  PIN9
  DB  00H, 00H, 00H , 00H ;#10 PBAT
  DB  00H, 00H, 00H , 00H ;#11 P220  NOT ACTIVE DELETED
  DB  01H, 00H, 60H , 61H ;#12 PGM1
  DB  01H, 00H, 62H , 63H ;#13 PGM2
  ;464 + 13x4  = 516
; ORG 516..520 GAP

; Comand filters     520 (  5 x 8 = 40) .. 559

 ; Group ADEMCO | RESERVE | RAJON | USER/ZONE
 ;  XXXX.XXXXB  |     XXH |   XXH |    XX XFH  5 bytes x 8 tlf numbers
 ; Group ADEMCO
 ; xxxx xxx1 Alarm          100 ..160 
 ; xxxx xx1x Supervision    200, 210 
 ; xxxx x1xx Trouble        300
 ; xxxx 1xxx Open/Close     400,440,450,460
 ; xxx1 xxxx Remote Access  410
 ; xx1x xxxx Access Control 420,430

 ; x1xx xxxx Bypass/Disable 500
 ; 1xxx xxxx Test/Miscelanious 600,700,900
 ; 0000 1011  01 00 FF  ; tlf1  =
 ; Alarm + Supervision + Open/Close  Rajon 01 Users 0..9 will be sent to tlf1
 ; RESERVE For more detailed groups
 ; Rajon 1..99,  User/zone 0 .. 999 last F. F is wildkart 00F0 all users/zones 0..9
  ORG 520
  DB FFH, FFH, FFH,  FFH, FFH    ; user tlf 1    Vse komandi
  ORG 525
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 2
  ORG 530
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 3
  ORG 535
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 4
  ORG 540
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 5
  ORG 545
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 6
  ORG 550
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 7
  ORG 555
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 8


;
;  560
;
; DALLAS 560 + 64  16 X 4 used 15  560 + 64 = 624
;
;    GAP  624 .. 629
;
    ORG 630
    DB   ' Door open 1',0
    ORG 650
    DB   'ARMED by user 2',0
    ORG 670
    DB   'Disarmed by user 3',0
    ORG 690
    DB   'Clock ready 4',0
    ORG 710
    DB   'Supper ready 5',0
    ORG 730
    DB   'XXX ready 6',0
    ORG 750
    DB   'HALLO 7',0
    ORG 770
    DB   'HALLO 8',0
    ORG 790
    DB   'HALLO 9',0
    ORG 810
    DB   'HALLO 10',0
    ORG 830
    DB   'HALLO 11',0
    ORG 850
    DB   'HALLO 12',0
    ORG 870
    DB   'HALLO 13',0
    ORG 890
    DB   'HALLO 14',0
    ORG 910
    DB   'HALLO 15',0
    ORG 930
    DB   'HALLO 16',0
    ORG 950
    DB   'HALLO 17',0
    ORG 970
    DB   'HALLO 18',0
    ORG 990
    DB   'HALLO 19',0
;SYSTEM ARRAY
;    1010, 1011 - Version
;    1012, 1013 - Data    EPROM Control sum 0 .. 533
;    1014, 1015 - Program EPROM Control sum
;    1016 .. 1021  6 byte PIN code
;    1022, 1023  Program Status Word for hot restart