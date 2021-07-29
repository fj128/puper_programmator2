# I gave up on importlib.
data = ''';E10MA00.ASM  E10 - version EPROM  MA - PANEL MAGELAN 00 SUBVERSION FOR mAGELAN
;MEMORY MAP
;06.08.2000  message groups changed to 8 in filter
;-------------------------------;
;   PN       J   U    M     P   E  R  = PN #3
;   D7 |  D6 | D5 | D4 | D3 | D2 | D1 | D0 |
;
; Back1 Back0 Ip1  Ip0  =  1  ;if IP1 = 1 -> reserve IP adress available
;
;PANEL tYPE: PUSHBUTON  0x00  DALLAS   0x01  Ademco 02 Magelan 03 Kodinis 4
; Esprit 5
     ORG     0000h       ; 38h,
;            AA   AA  TY  PN   HH      MM   KK  KK   PP   UU   U0
        DB   99h, 99h, 0, 06, 0Eh,   10H,  16h,02h, 00h, 00h, 00h, FFH


;-------------------------------;
;D7      |D6  |  D5  | D4   || D.3  | D.2     | D.1 |D.0
;1=Active|MESS|1=PGM2|1=PGM1||   x  | 1=24H   |     |0=NO
;
;        Th, Tl, Td     DD   0K_KK     0K_KK  PP     UU_U0
;                                       Alarm    Recovery
;                                       disarm   arm

      ORG 12
        DB       0, 0, 10 , 10000000B, 11H,30H, 31H, 30H, 00H, 00H, 10H, FFH   ;PIN1
      ORG 24    ;   Garaza 1
        DB       0, 0, 10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 20H, FFH   ;PIN2
      ORG 036   ;   Garaza 2
        DB       0, 0, 10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 30H, FFH   ;PIN3
      ORG 48    ;   Durvis
        DB       0, 0, 10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 40H, FFH   ;PIN4
      ORG 60    ;   Uguns trauksme
        DB       0, 0, 10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 50H, FFH   ;PIN5
      ORG 72    ;   Tamper
        DB       0, 0, 10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 60H, FFH   ;PIN6
      ORG 84    ;
        DB       0, 0, 10 , 10000100B, 11H,30H, 31H, 30H, 00H, 00H, 70H, FFH   ;PIN7
      ORG 96    ;   220 v
        DB       0, 0, 10 , 10000100B, 13H,00H, 33H, 00H, 00H, 00H, 80H, FFH   ;PIN8
      ORG 108
        DB       2, 0, 10 , 10000100B, 14H,00H, 34H, 00H, 00H, 00H, 00H, FFH   ;PIN9  ARM
      ORG 120
        DB       0, 0, 10 , 10000100B, 13H,02H, 33H, 02H, 00H, 00H, 00H, FFH   ;Pbat
; PGM1 PGM2
; TA arm/disarm 0.05 sek | TI pulse 0..20 x 0.05 sek 20..255 x 1 sek
; pin9 ON(ARm),  pin9 OFF(Disarm),  pinx ON , pinx OFF,
; DD     D.7 0 - notused,1-used|D.6 - 0| D.5 - 1=user|D.4 - 1=pin
;        D.3 - 0| D.2 - 0 |D.1 0-potential, 1-pulse| D.0(0=NO,1=NC)
     ORG     00132  ;5
        DB        0, 0, 0, 0,  00000011B        ;PGM1
     ORG     00137  ;5
        DB        0, 0, 0, 0,  00000001B        ;PGM2
;
    ORG 0142   ;16
    DB   '000.000.000.000',0             ; ip1 0FFh =cls 18
;    DB   '195.13.239.000',0,0,0h,0FFh              ; ip1 0FFh =cls 18
    ORG  158   ;5
    DB   '0000', 0,                              ; PORT1 0FFh =cls 8
    ORG 0163    ;20
    DB   '0000000000000000000',  0           ; Point1  0FFh =cls 14
    ;
    ORG 0183    ;16
    DB   '000.000.000.000',0               ;AP ip1 0FFh =cls 18
;    DB   '195.13.239.001',0,0h,0FFh              ;AP ip1 0FFh =cls 18
    ORG  0199    ;5
    DB   '0000', 0                          ; PORT1 0FFh =cls 8
    ORG  0204    ;20
    DB   '0000000000000000000', 0           ; Point1  0FFh =cls 14

    ORG     0224
;16x2  Backup numbers     224. (16*2) = 32   ..255
        DB   '00000000000',0,0,0,0,0  ;   BACKUP0
        DB   '00000000000',0,0,0,0,0  ;   BACKUP1
    ORG     0256
;16x8  User numbers     256 (16*8) = 128    .. 383

        DB   '00000000000',0,0,0,0,0  ;Tel. 1  37125921236
        DB   '00000000000',0,0,0,0,0  ;Tel. 2
        DB   '00000000000',0,0,0,0,0  ;Tel. 3
        DB   '00000000000',0,0,0,0,0  ;Tel. 4
        DB   '00000000000',0,0,0,0,0  ;Tel. 5
        DB   '00000000000',0,0,0,0,0  ;Tel. 6
        DB   '00000000000',0,0,0,0,0  ;Tel. 7
        DB   '00000000000',0,0,0,0,0  ;Tel. 8

       ORG     384       ;
; White tel numbers      384  (10 x 8 = 80) .. 463
; NN NN NN NN Dd  PP PP CLS
; NN NN NN NN  - 8 last digits
; Dd -Dd.3 PGM2   Dd.2 PGM1  Dd.1 Arm/disarm Dd.0 1 = PIN MAGELAN
; PP PP - Pin 4 digit
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 1
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 2
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 3
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 4
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 5
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 6
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 7
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 8
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 9
        DB   FFH, FFH, FFH, FFH, FFH, 0, FFH, FFH  ;Tel. 10

;    DB     00001111B                        ; 1 = Allowed Ip or Sim
; MESSAGE KROSS REFERENCE 464  (16 * 4 = 64)   .. 517
;       D0                         D1                        D2
; D7 D6 D5 D4 D3 D2 D1 D0 | D7 D6 D5 D4 D3 D2 D1 D0 | D7 D6 D5 D4 D3 D2 D1 D0 |
; T7 T6 T5 T4 T3 T2 T1 T0 | TF TE TD TC TB TA T9 T8 |  x  1  1    MESSAGE NR.
;                                                         |  |_ text MESSAGE
;                                                         |____ STANDART MESSAGE

  ORG 464
  ;
  DB  00H, 00H, 00H , 00H ;#1  PIN1
  DB  00H, 00H, 00H , 00H ;#2  PIN2
  DB  00H, 00H, 00H , 00H ;#3  PIN3
  DB  00H, 00H, 00H , 00H ;#4  PIN4
  DB  00H, 00H, 00H , 00H ;#5  PIN5
  DB  00H, 00H, 00H , 00H ;#6  PIN6
  DB  00H, 00H, 00H , 00H ;#7  PIN7
  DB  00H, 00H, 00H , 00H ;#8  PIN8
  DB  00H, 00H, 00H , 00H ;#9  PIN9
  DB  00H, 00H, 00H , 00H ;#10 PBAT
  DB  00H, 00H, 00H , 00H ;#11 P220
  DB  00H, 00H, 00H , 00H ;#12 PGM1
  DB  00H, 00H, 00H , 00H ;#13 PGM2
  ;464 + 13x4  = 516
ORG 516 ; 516..520 GAP
DB 0, 0, 0, 0

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
 ;             PP    GG   GF
  DB 00H, 00H, 00H,  00H, 0FH    ; user tlf 1    Vse komandi
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

  ORG 560
 DB 11H,11H,11H,11H, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH
  ORG 576
 DB FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH
  ORG 592    ;        1                2                3
    DB FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH
  ORG 608    ;        1                2                3
    DB FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH,FFH,FFH
;
    ;GAP 624 .. 629
  ORG 624   ;
    DB  FFH,FFH,FFH,FFH, FFH,FFH

    ORG 630
    DB      'Message  1',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH  ;0
    ORG 650
    DB      'Message  2',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH        ;1
    ORG 670
    DB      'Message  3',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH   ;2
    ORG 690
    DB      'Message  4',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH        ;3
    ORG 710
    DB      'Message  5',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH    ;4
    ORG 730
    DB      'Message  6',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH         ;5
    ORG 750
    DB      'Message  7',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH     ;6
    ORG 770
    DB      'Message  8',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH           ;7
    ORG 790
    DB      'Message  9',0,   FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH       ;8
    ORG 810
    DB      'Message 10',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH              ;9
    ORG 830
    DB      'Message 11',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH       ;10
    ORG 850
    DB      'Message 12',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH           ;11
    ORG 870
    DB      'Message 13',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH         ;12
     ORG 890
    DB      'Message 14',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH              ;13
    ORG 910
    DB      'Message 15',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH
    ORG 930
    DB      'Message 16',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH
    ORG 950
    DB      'Message 17',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH
    ORG 970
    DB      'Message 18',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH
    ORG 990
    DB      'Message 19',0,  FFH,FFH,FFH, FFH,FFH,FFH,FFH, FFH,FFH

;SYSTEM ARRAY
;    1010, 1011 - Version
;    1012, 1013 - Data    EPROM Control sum 0 .. 1010
;    1014, 1015 - Program EPROM Control sum
;    1014 .. 1016  6 digit PIN code
;   Program Status Word for hot restart
;    1021, ZONE_Is
;    1022  0x55 = ARMED,  0 = DISARMED
;    1023  Zone_Al     WAS ALARMS IN PREVIOS CYCLE RESETS ON ARM
     ORG 1010                                  ;1023
     DB   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0'''
