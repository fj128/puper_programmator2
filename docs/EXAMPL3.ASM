; V3
; MEMORY MAP
;-------------------------------;
;   JMP       J   U    M     P   E  R  = PN #3
;   D7 |  D6 | D5 | D4 | D3 | D2 | D1 | D0 |
;
; Back1 Back0 Ip1  Ip0  PARR  2SIM
;
;PN - PANEL tYPE: PUSHBUTON  0x00  DALLAS   0x01  Ademco 02
             Magelan      03  KODINIS  0x04
     ORG     0000h       ; 38h,
;            AA   AA  JMP   PN   HH    MM   KK  KK   PP  UU  U0  CLS
        DB   88h, 88h, 50h, 03h, 10h,  2Ch, 16h,02h, 00h, 00h, 00h
    DB (256-(12h+ 34h+ 0+  0+ 0 +5 + 63H+00H+ 11H+22H+20H))      ;CLS


;-------------------------------;
;D7      |D6  |  D5  | D4   || D.3  | D.2     | D.1 |D.0
;1=Active|MESS|1=PGM2|1=PGM1||   x  | 1=24H   |     |0=NO,1=NC
;
;               Th, Tl, Td    DD       0K_KK    0K_KK    PP   UU_U0
;                                       Alarm    Recovery
;                                       arm      disarm
      ORG 12                       ;    close    open
        DB       0,  0, 10, 10000101B, 11H,30H, 31H,30H, 00H, 00H, 00H    ;PIN1
        DB 0 ;CLS
      ORG 24
        DB       0, 10, 10, 10000101B, 11H,20H, 31H,20H, 01H, 00H, 00H    ;PIN2
        DB 0 ;CLS
      ORG 036
        DB       0, 10, 10, 10000101B, 11H,20H, 31H,20H, 02H, 00H, 00H    ;PIN3
        DB 0 ;CLS
      ORG 48
        DB       0,  0, 10, 10000101B, 11H,10H, 31H,10H, 00H, 00H, 00H    ;PIN4
        DB 0
       ORG 60
        DB       0,  0, 10, 10000101B, 16H,11H, 16H,11H, 00H, 00H, 00H    ;PIN5
        DB 0 ;CLS
       ORG 72
        DB       0,  0, 10, 10000101B, 11H,30H, 31H,30H, 00H, 00H, 10H    ;PIN6
        DB 0 ;CLS
       ORG 84
        DB      60, 60, 10, 10000101B, 13H,01H, 33H,01H, 00H, 00H, 00H    ;PIN7
        DB 0 ;CLS
       ORG 96
        DB       0,  5, 10, 10000101B, 11H,44H, 31H,44H, 00H, 00H, 00H    ;PIN8
        DB 0 ;CLS
       ORG 108
      ; ARM  DISARM
        DB      10,  0, 10, 10010000B, 14H,00H, 34H,00H, 00H, 00H, 00H    ;PIN9
        DB 0 ;CLS
       ORG 120
        DB       0, 21, 10, 10000100B, 13H,02H, 33H,02H, 00H, 00H, 00H    ;Pbat
        DB 0 ;CLS
; PGM1 PGM2          Timer(0..20)x50 ms  20 + 1 cek
; TA arm/disarm 0.1 sek | TI pulse 0..20 x 0.1 sek 20..255 x 1 sek
; pin0 ON  pin0 OFF  pinx ON  pinx OFF
; D7    |D.6| D.5 |D4 |D3 |D2 | D1          |D0
;1-used | 0 |1=SMS|PIN|0  |0  | 0-pot,1-puls|0=NO,1=NC
     ORG     00132    ;5
        DB        5, 5,  30, 0, 10110011B        ;PGM1
     ORG     00137    ;5
        DB       10, 5, 40, 30, 10110001B       ;PGM2
;
;
    ORG 0142   ;16
    DB   '95.56.254.234',0,0,0h,0FFh              ; ip1 0FFh =cls 18
;    DB   '195.13.239.000',0,0,0h,0FFh              ; ip1 0FFh =cls 18
    ORG  158   ;5
    DB   '3012', 0,                              ; PORT1 0FFh =cls 8
    ORG 0163    ;20
    DB   'internet.beeline.kz', 0          ; Point1  0FFh =cls 14
    ;
    ORG 0183    ;16
    DB   '91.135.195.146',0,0h,0FFh              ;AP ip1 0FFh =cls 18
;    DB   '195.13.239.001',0,0h,0FFh              ;AP ip1 0FFh =cls 18
    ORG  0199    ;5
    DB   '3012', 0,0,0,0FFh                          ; PORT1 0FFh =cls 8
    ORG  0204    ;20
    DB   'internet.tele2.kz', 0, 0           ; Point1  0FFh =cls 14

    ORG     0224
;16x16  User numbers     224. (16*10) = 160 384
        DB   '77717050074',0,0,0,0,0  ;Tel. 1   BACKUP0
        DB   '77717050074',0,0,0,0,0  ;Tel. 2   BACKUP1
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
        DB   FFH, FFH, 79H, 01H, 99H, 6H, 12H, 34H  ;Tel. 1
        DB   FFH, FFH, 70H, 08H, 0EH, 6H, 12H, 34H  ;Tel. 2
        DB   FFH, FFH, 41H, 27H, 43H, 6H, 12H, 34H  ;Tel. 2
        DB   FFH, FFH, 23H, 28H, 24H, 6H, 12H, 34H  ;Tel. 2
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 5
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 6
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 7
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 8
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 9
        DB   0, 0, 0, 0, 0, 0, 0, 0  ;Tel. 10

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
  DB  04H, 00H, 65H , 66H ;#16 COMAND Filtr 3

;
; Comand filters     632 (  15 x 3 = 45) 677
  ORG 632   ;F = any nibl ;  KOMAND =  FQ KK KR RZ ZZ   = 1+9 NIBLS  5 BYTES
  ;                          FILTR  =  FFFF FF FFF F - first NIBL IS ALWAYS F
  ;  FQ   KK   KR    RZ   ZZ ; KK   RR    ZZ   ZZ  ;QK   KK   RR    ZZ   ZZ
  DB F4H, FFH, FFH,  FFH, FFH, 00H,  00H, 00H, 00H, 00H, 00H, 00H,  00H, 00H, 00H  ;#1
  ORG 647   ;Filtr 2
  DB 00H, 00H, FFH,  FFH, FFH, 00H,  00H, 00H, 00H, 00H, 00H, 00H,  00H, 00H, 00H  ;#1
  ORG 662  ;Filtr 3
  DB 00H, 00H, FFH,  FFH, FFH, 00H,  00H, 00H, 00H, 00H, 00H, 00H,  00H, 00H, 00H  ;#1
;

;   16 x 20 symbols soobchenija po
    ORG 680
    DB   ' Door open 0',0
    ORG  700
    DB   'ARMED by user 1',0
    ORG  720
    DB   'Disarmed by user 2',0
    ORG  740
    DB   'Clock ready 3',0
    ORG  760
    DB   'Supper ready 4',0
    ORG  780
    DB   'XXX ready 5',0
    ORG  800
    DB   'HALLO 6',0