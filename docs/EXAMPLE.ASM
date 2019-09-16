;MEMORY MAP
;-------------------------------;
;   PN       J   U    M     P   E  R
;   D7 |  D6 | D5 | D4 | D3 | D2 | D1 | D0 |
;
; Back1 Back0 Ip1  Ip0  PARR PANEL tYPE  0-SWITCH 1 - DALLAS 2-ADEMCO
;

     ORG     0000h       ; 38h,
;            AA   AA  TY  PN   HH    MM   KK  KK   PP  UU  U0  CLS
        DB   12h, 34h, 0, 53h, 10h,  2Ch, 16h,02h, 00h, 00h, 00h
    DB (256-(12h+ 34h+ 0+  0+ 0 +5 + 63H+00H+ 11H+22H+20H))      ;CLS


;-------------------------------;
;D7          |D6  |   D5  | D4   |D.3|  D.2 | D.1       |D.0
;1=pin active MESS     x    x    1=PGM2 1=PGM  1=24H      0=NO,1=NC
;            MESS
;        Th, Tl, Td     DD   0K_KK     0K_KK  PP     0U_UU
;                                       Alarm     Recovery
;                                       Disarm   Arm
      ORG 12
        DB       10, 2, 5 , 10010000B, 34H,07H, 14H, 07H, 00H, 00H, 00H   ;PIN1
        DB 0 ;CLS
      ORG 24
        DB       2,  2, 5 , 10010000B, 11H,30H, 31H, 30H,02H, 01H, 20H   ;PIN2
        DB 0;CLS
      ORG 036
        DB       2, 2, 5 ,  10100100B, 11H,30H, 31H, 30H, 03H, 01H, 30H   ;PIN3
        DB 0 ;CLS
      ORG 48
        DB       2, 2, 5 ,  10000000B, 11H,30H, 31H, 30H, 04H, 01H, 40H  ;PIN4
       ORG 60
        DB       2, 2, 5 ,  10000000B, 11H,30H, 31H, 30H, 05H, 01H, 50H   ;PIN5
        DB 0 ;CLS
       ORG 72
        DB       2, 2, 5 ,  10000000B, 11H,30H, 31H, 30H, 06H, 01H, 60H   ;PIN6
        DB 0 ;CLS
       ORG 84
        DB       2, 2, 5 , 10000000B, 11H,30H, 31H, 30H, 07H, 01H, 70H   ;PIN7
        DB 0;CLS
       ORG 96
        DB       2, 2 , 5 , 10000000B, 11H,30H, 31H, 30H, 08H, 01H, 80H   ;PIN8
        DB 0 ;CLS
       ORG 108
        DB       1, 2, 5 , 10000000B, 11H,30H, 31H, 30H, 09H, 01H, 90H   ;PIN9
        DB 0 ;CLS
       ORG 120
        DB       10, 20, 5 , 10000000B, 13H,11H, 33H, 11H, 00H, 00H, 00H   ;Pbat
        DB 0 ;CLS
; PGM1 PGM2
; TA arm/disarm 0.1 sek | TI pulse 0..20 x 0.1 sek 20..255 x 1 sek
; pin0 ON  pin0 OFF  pinx ON  pinx OFF
; DD     D.7 0 - notused,1-used|D.6 - 0| D.5 - 1=user|D.4 - 1=pin
;        D.3 - 0| D.2 - 0 |D.1 0-potential, 1-pulse| D.0(0=NO,1=NC)
     ORG     00132
        DB       10, 5, 60, 30, 10110011B        ;PGM1
        DB (256-(5+ 30+ 06H))      ;CLS
     ORG     00138
        DB       10, 5, 40, 30, 10110001B       ;PGM2
        DB (256-(5+ 30+ 06H))      ;CLS
;
;
    ORG 0144   ;18
    DB   '195.13.239.242',0,0,0h,0FFh              ; ip1 0FFh =cls 18
;    DB   '195.13.239.000',0,0,0h,0FFh              ; ip1 0FFh =cls 18
    ORG  162   ;5
    DB   '3301', 0,                              ; PORT1 0FFh =cls 8
    ORG 0167    ;17
    DB   'internet', 0, 0, 0, 0, 0, 0FFh    ; Point1  0FFh =cls 14
    ;
    ORG 0184    ;18
    DB   '195.13.239.243',0,0h,0FFh              ;AP ip1 0FFh =cls 18
;    DB   '195.13.239.001',0,0h,0FFh              ;AP ip1 0FFh =cls 18
    ORG  0202    ;5
    DB   '3000', 0,0,0,0FFh                          ; PORT1 0FFh =cls 8
    ORG  0207    ;17
    DB   'internet.lmt.lv', 0, 0           ; Point1  0FFh =cls 14

    ORG     0224
;16x16  User numbers     224. (16*10) = 160 384
        DB   '37129287008',0,0,0,0,0  ;Tel. 1   BACKUP0
        DB   '37129287008',0,0,0,0,0  ;Tel. 2   BACKUP1
        DB   '37129287008',0,0,0,0,0  ;Tel. 3
        DB   '37129287008',0,0,0,0,0  ;Tel. 4
        DB   '37129287008',0,0,0,0,0  ;Tel. 5
        DB   '37129287008',0,0,0,0,0  ;Tel. 6
        DB   '37129287008',0,0,0,0,0  ;Tel. 7
        DB   '37129287008',0,0,0,0,0  ;Tel. 8
        DB   '37129287008',0,0,0,0,0  ;Tel. 9
        DB   '37129287008',0,0,0,0,0  ;Tel. 10

       ORG     384       ;
; White tel numbers      384  (10 x 12 = 120) .. 504
; NN NN NN NN Dd  PP PP CLS
; NN NN NN NN  - 8 last digits
; Dd -Dd.3 PGM2   Dd.2 PGM1  Dd.1 Arm/disarm Dd.0 1 = PIN
; PP PP - Pin 4 digit
        DB   '1234567',  0  ;Tel. 1
        DB   '8912345',  0  ;Tel. 2
        DB   '3332221',  0  ;Tel. 3
        DB   '9287008',  0  ;Tel. 4
        DB   '9232824',  0  ;Tel. 5
        DB   '#######',  0  ;Tel. 6
        DB   '#######',  0  ;Tel. 7
        DB   '#######',  0  ;Tel. 8
        DB   '#######',  0  ;Tel. 9
        DB   '#######',  0  ;Tel. 10

;    0RG 504  (64) 568
;    DB     00001111B                        ; 1 = Allowed Ip or Sim
; DALLAS  64  16 X 4 used 15
    ORG 568
; MESSAGE KROSS REFERENCE 568  (16 * 4 = 64)   .. 632
;       D0                         D1                        D2
; D7 D6 D5 D4 D3 D2 D1 D0 | D7 D6 D5 D4 D3 D2 D1 D0 | D7 D6 D5 D4 D3 D2 D1 D0 |
; T7 T6 T5 T4 T3 T2 T1 T0 | TF TE TD TC TB TA T9 T8 |  x  1  1    MESSAGE NR.
;                                                         |  |_ text MESSAGE
;                                                         |____ STANDART MESSAGE
;                                                     |_ STANDART MESSAGE

  DB  01H, 00H, 60H , 61H ;#1  PIN1 rec T1 MES STAND + TXT 0| Alarm
  DB  02H, 00H, 62H , 63H ;#2  PIN2
  DB  04H, 00H, 64H , 65H ;#3  PIN3
  DB  08H, 00H, 65H , 60H ;#4  PIN4
  DB  01H, 00H, 60H , 60H ;#5  PIN5
  DB  01H, 00H, 60H , 60H ;#6  PIN6
  DB  01H, 00H, 60H , 60H ;#7  PIN7
  DB  01H, 00H, 60H , 60H ;#8  PIN8
  DB  01H, 00H, 60H , 60H ;#9  PIN9
  DB  01H, 00H, 00H , 00H ;#10 PBAT
  DB  01H, 00H, 00H , 00H ;#11 P220
  DB  01H, 00H, 00H , 00H ;#12 PGM1
  DB  01H, 00H, 00H , 00H ;#13 PGM2
  DB  01H, 00H, 61H , 62H ;#14 COMAND Filtr 1
  DB  02H, 00H, 63H , 64H ;#15 COMAND Filtr 2
  DB  04H, 00H, 65H , 64H ;#16 COMAND Filtr 3

;
; Comand filters     632 (  15 x 3 = 45) 677
  ORG 632   ;F = any nibl ;  KOMAND =  QKKK RR ZZZ   = 9 NIBLS  5 BYTES
  ;                          FILTR  =  FFFF FF FFF F - LAST NIBL IS ALWAYS F
  ;  QK   KK   RR    ZZ   ZZ ; QK   KK   RR    ZZ   ZZ  ;QK   KK   RR    ZZ   ZZ
  DB F4H, FFH, FFH,  FFH, FFH, 00H,  00H, 00H, 00H, 00H, 00H, 00H,  00H, 00H, 00H  ;#1
  ORG 647   ;Filtr 2
  DB 00H, 00H, FFH,  FFH, FFH, 00H,  00H, 00H, 00H, 00H, 00H, 00H,  00H, 00H, 00H  ;#1
  ORG 662  ;Filtr 3
  DB 00H, 00H, FFH,  FFH, FFH, 00H,  00H, 00H, 00H, 00H, 00H, 00H,  00H, 00H, 00H  ;#1
;

;   16 x 20 symbols soobchenija po
    ORG 680
    DB   '  0 door open',0
    ORG  700
    DB   ' ARMED by user ',0
    ORG  720
    DB   ' Disarmed by user',0
    ORG  740
    DB   '  3 5 Oclock  ready',0
    ORG  760
    DB   '  4 Supper ready',0
    ORG  780
    DB   '  5 PUSSY ready',0
    ORG  800
    DB   '  6  HALLO',0