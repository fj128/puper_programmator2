#pragma debug code OE
/* ���ᠭ�� ॣ���஢ AT89C5131 */


#include "INC\i5131.h"
#include <reg5131.h>

/* ���ᠭ�� ����⠭� ��� ����㯠 � ॣ���ࠬ */
#include "INC\ext_5131.h"

#include "types.h"
#include "const.h"
#include "reg_macr.h"
#include "descript.h"
#include "test.h"

#include "usb_util.h"
#include "usb_enu2.h"
//#include "usb_func.h"
sbit PGM1     =   0xA5;        //p2.5   #4
sbit PGM2     =   0xA4;        //p2.4   #3
sbit PIN1     =   0x92;        //p1.2
bit F_Output;
unsigned char ttt, zzz,T10ms,Timeout_USB,F_USB_Inp,InputByte_nn;
unsigned char idata InputString[23],OutputString[23];
unsigned int XM_Adr;
//UsbFunkc.h
//extern void UsbInit();

extern unsigned char Read_EPROM_char(void);                            /* define 8051 registers */
extern unsigned char Write_EPROM_char(void);                            /* define 8051 registers */
extern void          PROG_WAIT_EPROM(void);

extern void UsbControlPacketProcessed();
extern void GetStatusDevice();
extern void GetStatusInterface();
extern void GetStatusEndpoint();
extern void GetDescriptor();
extern void GetConfiguration();
extern void SetConfiguration();
extern void SetAddress();
extern byte * usb_send_ep0_packet(byte* tbuf, byte data_length);
code char xxx[10]   = {"HALLO   \xA\xD"};
code char yyy[30]   = {"HALLO USB->serial 32 bytes \xA\xD"};
code char ccc[12]    = {":E10112345F\xD"};
                                                                 //88  78
/* =================================================== */
/*                    ���樠������ USB                */
/* =================================================== */
/*
   -----------------------------------------------------
   �ᮡ�� �������� ᫥��� ������ �� ���樠������ PLL
   ������� PLL_xxHz ������ ᮮ⢥��⢮���� �ᯮ����-
   ���� ������. ���� ���ன�⢮ �� �㤥� ������������
   � Windows.
   -----------------------------------------------------
*/
 void intt0 () interrupt 1
{ unsigned char i;
   T10ms--;
if ( T10ms == 0 )
    {  T10ms = 96;
       if ( Timeout_USB != 0 )
       {    Timeout_USB --; }
    }
}

void SendRS232(char ch)
{
 while(!TI);
 TI=0;
 SBUF = ch;
 while(TI);
}
unsigned char Ch_Ascii (unsigned char aaa)
//Transform aaa (0..15) to '0'..'9','A'..'F'
{
    aaa = aaa & 0x0F;
    if (( aaa >= 0) && ( aaa <= 9))
          {aaa =  aaa + '0';}
    else
    {  aaa =  aaa - 10 + 'A';  }
    return aaa;
}
void Put_char_Asci ( unsigned char ccc,ddd )
{ unsigned char aaa;
      aaa = Ch_Ascii (ccc/16);  SendRS232(aaa);
      aaa = Ch_Ascii (ccc%16);  SendRS232(aaa);
      aaa = ddd; SendRS232(aaa);
}
void cdc_init()
{
  /* ���䨣��஢���� RS232 */
  SCON    = MSK_UART_8BIT;
  CKCON0 |= MSK_X2;
  PCON   |= MSK_SMOD1;
  BDRCON |= 2;
  BDRCON |= 0x1C;
  BDRCON &= ~1;
  BRL     = 100;
  SCON   |= MSK_UART_ENABLE_RX|MSK_UART_TX_READY|MSK_UART_ENABLE_RX;

  line_coding[0] = 0x00;
  line_coding[1] = 0xC2;
  line_coding[2] = 0x01;
  line_coding[3] = 00;
  line_coding[4] = 0;    /* stop bit  */
  line_coding[5] = 0;    /* parity    */
  line_coding[6] = 8;    /* data bits */

  CDCLineState = 0;
  tx_counter=0;
}

void cdc_set_line_coding()
{
  WaitForFillFIFO();

  line_coding[0] = Usb_read_byte();    Put_char_Asci(line_coding[0],'!');
  line_coding[1] = Usb_read_byte();    Put_char_Asci(line_coding[1],'!');
  line_coding[2] = Usb_read_byte();    Put_char_Asci(line_coding[2],'!');
  line_coding[3] = Usb_read_byte();    Put_char_Asci(line_coding[3],'!');
  line_coding[4] = Usb_read_byte();    Put_char_Asci(line_coding[4],'!');
  line_coding[5] = Usb_read_byte();    Put_char_Asci(line_coding[5],'!');
  line_coding[6] = Usb_read_byte();    Put_char_Asci(line_coding[6],'!');
  EndReadData();

  SendInZeroPacket();
}


void cdc_get_line_coding()
{
  Usb_set_DIR();

  Usb_write_byte(line_coding[0]);    Put_char_Asci(line_coding[0],'!');
  Usb_write_byte(line_coding[1]);    Put_char_Asci(line_coding[1],'!');
  Usb_write_byte(line_coding[2]);    Put_char_Asci(line_coding[2],'!');
  Usb_write_byte(line_coding[3]);    Put_char_Asci(line_coding[3],'!');
  Usb_write_byte(line_coding[4]);    Put_char_Asci(line_coding[4],'!');
  Usb_write_byte(line_coding[5]);    Put_char_Asci(line_coding[5],'!');
  Usb_write_byte(line_coding[6]);    Put_char_Asci(line_coding[6],'!');
  SendDataFromFIFO();

  WaitForOutZeroPacket();
}

void cdc_set_control_line_state()
{
  SendInZeroPacket();
  if (SetupPacket.b[2] == 0) {end_point1_ready = 0;}   //TEST
}

void cdc_send_break()
{
  SendInZeroPacket();
}

void cdc_send_encapsulated_command (void)
{
}

void cdc_get_encapsulated_command (void)
{
}

void usb_init()
{
 /* ���樠������ PLL */
 Pll_set_div(PLL_24MHz);
 Pll_enable();

 /* ����祭�� USB */
 Usb_enable();

 /* �⪫������-����������� ��� ��砫� �㬥�樨 */
 Usb_detach();
 delay5();
 Usb_attach();
 delay5();

 /* ���䨣��஢���� �㫥��� ����筮� �窨 */
 usb_configure_endpoint(0, CONTROL|MSK_EPEN);
 usb_reset_endpoint(0);

 /* ����� ���䨣��樨 */
 usb_configuration_nb = 0x00;

 end_point1_ready = 0;
}


/* =================================================== */
/*                  ��ࠡ�⪠ control-�����           */
/* =================================================== */
/*
   -----------------------------------------------------
   ���⮨� �� ��� 䠧: Setup, Data, Status.
   ��ࠡ�⪠ ��稭����� �� ����祭�� setup-�����.
   ���� Data ����� ������⢮����.
   -----------------------------------------------------
*/
void UsbControlPacketProcessed()
{
  /* ------------------------------ */
  /*       ��⠥� setup-�����       */
  /* ���⮨� �� 8 ���� (�. 1.2.1): */
  /*  [0] byte bmRequestType        */
  /*  [1] byte bRequest             */
  /*  [2] word wValue               */
  /*  [4] word wIndex               */
  /*  [6] word wLength              */
  /* ------------------------------ */
  for (i=0; i<8; i++)
   SetupPacket.b[i]= Usb_read_byte();

  /* ---------------------------------- */
  /* �����襭�� setup-䠧�. ���� FIFO. */
  /* ---------------------------------- */
  EndSetupStage();

  /* ---------------------------- DEBUG */
  for (i=0; i<8; i++)
   Put_char_Asci(SetupPacket.b[i],'.');

  /* ------------------------------ */
  /*         ��ࠡ�⪠ �����      */
  /* ------------------------------ */
  switch (SetupPacket.wRequest)
  {
    case GET_STATUS_DEVICE:    //0x8000
     GetStatusDevice();
     break;

    case GET_STATUS_INTERF:    //0x8100
     GetStatusInterface();
     break;

    case GET_STATUS_ENDPNT:    //0x8200
     GetStatusEndpoint();
     break;

    case GET_DESCRIPTOR_DEVICE:    //0x8006
    case GET_DESCRIPTOR_INTERF:    //0x8106
    case GET_DESCRIPTOR_ENDPNT:    //0x8206
     GetDescriptor();
     break;

    case GET_CONFIGURATION:       //0x8008
     GetConfiguration();
     break;

    case SET_CONFIGURATION:      //0x0009
     SetConfiguration();
     break;

    case SET_ADDRESS:            //0x0005
     SetAddress();
     break;
    /* CDC Specific requests */
    case SET_LINE_CODING:        //0x2120
      cdc_set_line_coding();
      break;
    case GET_LINE_CODING:        //0xA121
      cdc_get_line_coding();
      break;
    case SET_CONTROL_LINE_STATE:     //0x2122
      cdc_set_control_line_state();
      break;
    case SEND_BREAK:
      cdc_send_break();             //0x2123
      break;
    case SEND_ENCAPSULATED_COMMAND:
      cdc_send_encapsulated_command();      //0x2100
      break;
    case GET_ENCAPSULATED_COMMAND:
      cdc_get_encapsulated_command();      //0xA101
      break;

    default:
     STALL();
     break;
  }

}

/* =================================================== */
/*  GetStatusXxx                                       */
/*     - ᫮�� ���ﭨ� ���ன�⢠                    */
/*     - ᫮�� ���ﭨ� ����䥩�                    */
/*     - ᫮�� ���ﭨ� ����筮� �窨                */
/* (�. ࠧ��� 1.2.2)                                  */
/* =================================================== */
void GetStatusDevice()
{
  Usb_set_DIR();

  /*
    ���ன�⢮ ��।��� ��� ���� ������:
    � ���� 0 �ᯮ������ ��� ���:
     [1]= 0: ���ன�⢮ �������� ᨣ��� ���㤪�
     [0]= 0: ���ன�⢮ ����砥� ��⠭�� �� 設� USB
    ���� 1 ��१�ࢨ஢�� � �ᥣ�� ࠢ�� 0.
  */
  Usb_write_byte(0x00);  Put_char_Asci(0x00,'!');
  Usb_write_byte(0x00);  Put_char_Asci(0x00,'!');
  SendDataFromFIFO();

  WaitForOutZeroPacket();
}

void GetStatusInterface()
{
  Usb_set_DIR();

  /*
     ���ன�⢮ ��।��� ��� ���� ������,
     (᫮�� ���ﭨ� ���ன�⢠). ��� ����
     ��१�ࢨ஢��� � ࠢ�� ���.
  */
  Usb_write_byte(0x00);  Put_char_Asci(0,'!');
  Usb_write_byte(0x00);  Put_char_Asci(0,'!');
  SendDataFromFIFO();

  WaitForOutZeroPacket();
}

void GetStatusEndpoint()
{
  data byte wIndex;

  /* ����� ����筮� �窨 � ����襬 ���� wIndex */
  wIndex = SetupPacket.b[4] & MSK_EP_DIR;

  Usb_set_DIR();
  /*
     ���ன�⢮ ��।��� ��� ���� ������.
     �ᯮ������ ⮫쪮 ���� ��� ��ࢮ�� ����:
       0 - ����筠� �窠 �㭪樮����� ��ଠ�쭮
       1 - ��।�� ������ �������஢���
     ��⠫�� ���� ࠧ��ࢮ�஢��� � ࠢ�� 0.
  */
  Usb_write_byte(0x00);    Put_char_Asci(0,'!');
  Usb_write_byte(0x00);    Put_char_Asci(0,'!');
  SendDataFromFIFO();

  WaitForOutZeroPacket();
}

/* =================================================== */
/*                    GetDescriptor                    */
/* =================================================== */
void GetDescriptor()
{
 data byte    data_to_transfer;
 data uint16  wLength;
 bit          zlp;
 data byte   *pbuffer;

 zlp = FALSE;

 /* ��� ����訢������ ���ਯ�� ��室����  */
 /* � ���襬 ���� ���� wValue, �.�. ���� 3 */
 switch (SetupPacket.b[3])
 {
    /* ���ਯ�� ���ன�⢠ */
    case DEVICE:    //0x01
    {
      data_to_transfer = sizeof(usb_device_descriptor);
      pbuffer = &(usb_device_descriptor.bLength);
      break;
    }
    /* ���ਯ�� ���䨣��樨 */
    case CONFIGURATION:    //0x02
    {
      data_to_transfer = sizeof(usb_configuration);
      pbuffer = &(usb_configuration.cfg.bLength);
      break;
    }
    /* ���ਯ�� ��ப� */
    case STRING:           //0x03
    {
      /* ������ ��ப� ��室���� � ����襬 */
      /* ���� ���� wValue, �.�. ���� 2   */
      switch (SetupPacket.b[2])
      {
        case LANG_ID:            // 0x00
        {
          data_to_transfer = sizeof (usb_language);
          pbuffer = &(usb_language.bLength);
          break;
        }
        case MAN_INDEX:         //0x01
        {
          data_to_transfer = sizeof (usb_manufacturer);
          pbuffer = &(usb_manufacturer.bLength);
          break;
        }
        case PRD_INDEX:        //0x02
        {
          data_to_transfer = sizeof (usb_product);
          pbuffer = &(usb_product.bLength);
          break;
        }
        case SRN_INDEX:       //0x03
        {
          data_to_transfer = sizeof (usb_serial_number);
          pbuffer = &(usb_serial_number.bLength);
          break;
        }
        default:
        {
          STALL();
          return;
        }
      }
      break;
    }

    default:
    {
      STALL();
      return;
    }
  }

  /* �⥭�� �ॡ㥬��� �᫠ ���� */
  /* (���� wLenght)               */
  wLength = wSWAP(SetupPacket.setup.wLength);


  /* �ॡ���� ����� 祬 ����? */
  if (wLength > data_to_transfer)
  {
    /* �᫨ �᫮ ���� ����� ��⭮ ࠧ���� �����, */
    /* � ����� �����襭�� �ନ�㥬 ᯥ樠�쭮      */
    if ((data_to_transfer % EP_CONTROL_LENGTH) == 0)
    {
     zlp = TRUE;
    }
    else
    {
     zlp = FALSE;
    }
  }
  else
  {
    /* ���뫠�� ⮫쪮 �ॡ㥬�� �᫮ ���� */
    /* ������ �� �����, 祬 ���� ॠ�쭮  */
    /* ������� �� ����� �� �ॡ����        */
    data_to_transfer = (byte)wLength;
  }

  /* ��४��祭�� ���ࠢ����� �㫥��� �窨 */
  Usb_set_DIR();

  /* 諥� ���� 墠⠥� ������ �� �ନ஢���� ������� ����� */
  /* ���⮪ ����� ���뫠�� ��⮬ (�᫨ ����)               */
  while (data_to_transfer > EP_CONTROL_LENGTH)
  {
    /* ��।�� ���� ���ᨬ��쭮� �����*/
    pbuffer = usb_send_ep0_packet(pbuffer, EP_CONTROL_LENGTH);
    /* ᤢ����� 㪠��⥫� */
    data_to_transfer -= EP_CONTROL_LENGTH;

    /* ���� �����襭�� ��।�� */
    Usb_set_tx_ready();
    while ((!(Usb_rx_complete())) && (!(Usb_tx_complete())));
    Usb_clear_tx_complete();
    if ((Usb_rx_complete())) /* �᫨ ��।�� ��ࢠ�� ��⮬ */
    {
      Usb_clear_tx_ready(); /* �������� ��।��� */
      Usb_clear_rx();
      return;
    }
  }

  /* ���뫠�� ������ ����� ������          */
  /* �᫨ ⠪�� ����� �������, � �� ���� */
  /* ����⮬ �����襭�� ��।��               */
  pbuffer = usb_send_ep0_packet(pbuffer, data_to_transfer);
  data_to_transfer = 0;
  Usb_set_tx_ready();
  while ((!(Usb_rx_complete())) && (!(Usb_tx_complete())));
  Usb_clear_tx_complete();
  if ((Usb_rx_complete())) /* �᫨ ��।�� ��ࢠ�� ��⮬ */
  {
    Usb_clear_tx_ready();
    Usb_clear_rx();
    return;
  }

  /* �� ����室����� (�᫨ �� ������ �����)       */
  /* �ନ�㥬 ����� �����襭�� ᯥ樠�쭮 - ���뫪�� */
  /* ����� �㫥��� �����                             */
  if (zlp == TRUE)
  {
    usb_send_ep0_packet(pbuffer, 0);
    Usb_set_tx_ready();
    while ((!(Usb_rx_complete())) && (!(Usb_tx_complete())));
    Usb_clear_tx_complete();
    if ((Usb_rx_complete())) /* �᫨ ��।�� ��ࢠ�� ��⮬ */
    {
      Usb_clear_tx_ready();
      Usb_clear_rx();
      Usb_clear_DIR();
      return;
    }

  }

  while ((!(Usb_rx_complete())) && (!(Usb_setup_received())));
  if (Usb_setup_received())
  {
    return;
  }

  if (Usb_rx_complete())
  {
    Usb_clear_DIR();  /* ��४��祭�� ���ࠢ����� 0 �窨 */
    Usb_clear_rx();
  }

}

/* =================================================== */
/*                  GetConfiguration                   */
/* =================================================== */
void GetConfiguration()
{
  Usb_set_DIR();

  /*
    ���ன�⢮ ��।��� ���� ���� ������,
    ᮤ�ঠ騩 ��� ���䨣��樨 ���ன�⢠.
  */
  Usb_write_byte(usb_configuration_nb);  Put_char_Asci(usb_configuration_nb,'!');
  SendDataFromFIFO();

  WaitForOutZeroPacket();
}

/* =================================================== */
/*                  SetConfiguration                   */
/* =================================================== */
void SetConfiguration()
{
  data byte configuration_number;

  /* ���� ����� ���䨣��樨 */
  /* �� ����襣� ���� wValue  */
  configuration_number = SetupPacket.b[2];

  /* �᫨ ��࠭� ����㯭�� ���䨣���� */
  if (configuration_number <= CONF_NB)
  {
    /* ��࠭��� ����� ���䨣��樨 */
    usb_configuration_nb = configuration_number;
  }
  else
  {
    /* �訡��� ����� - �⪫��塞 */
    STALL();
    return;
  }

  /* 䠧� status */
  SendInZeroPacket();

  /* ���䨣��஢���� ��㣨� ������� �祪 */
  usb_configure_endpoint(1 , BULK_IN);   //  0x86
  usb_reset_endpoint(1);
  Usb_enable_ep_int(1);

  usb_configure_endpoint(2 , BULK_OUT);  // 0x82
  usb_reset_endpoint(2);
  Usb_enable_ep_int(2);

  usb_configure_endpoint(3 , INTERRUPT_IN); // 0x87
  usb_reset_endpoint(3);
  Usb_enable_ep_int(3);
}

/* =================================================== */
/* ��⠭���� ���� ���ன�⢠                         */
/* =================================================== */
void SetAddress()
{
  /* ���⠢��� 䫠� "���ன�⢮ ���ᮢ���" */
  Usb_set_FADDEN();
  SendInZeroPacket();
  /*
    ���� ��।��� ���� ���ன�⢠ � ����襩 ���
    ���� wValue.
  */
  Usb_configure_address(SetupPacket.b[2]);
}

/* =================================================== */
/*   ��।�� ����� �� �㫥��� ����筮� �窥         */
/* =================================================== */
byte * usb_send_ep0_packet(byte* tbuf, byte data_length)
{
  data int  i;
  data byte b;

  Usb_select_ep(0);

  for (i=0; i<data_length; i++)
  {
   b = *tbuf;
   Usb_write_byte(b);  Put_char_Asci(b,'!');
   tbuf++;
  }
  return tbuf;
}

/* ================================= */
/* MAIN - �᭮���� �㭪�� �ணࠬ�� */
/* ================================= */
void delay5()
{data unsigned int i;
 data unsigned int j;
 for (i=0; i<2000; i++) {j++;}
}
void print_descriptor(void)
{ data byte   *pbuffer;
  data byte   data_to_transfer,i,b;

      data_to_transfer = 18;//sizeof(usb_device_descriptor);
      pbuffer = &(usb_configuration.cfg.bLength);
  for (i=0; i< data_to_transfer; i++)
  {
   b = *pbuffer;
   Put_char_Asci(b,'?');
   pbuffer++;
  }

}
void main_task()
{ unsigned char j;
 /* ���ன�⢮ �� ��⮢� � ��।�� ������ */
 if ((usb_configuration_nb == 0) || (Usb_suspend()))
  return;

 if (end_point1_ready == 0) /* �।��騩 ����� ��ࠢ��� */
 { j = (OutputString[1] & 0x01F) + 6; //test
   if ( j > 22 )  { j = 22;}
   Usb_select_ep(1);
   for (i = 0; i <= j; i++) {Usb_write_byte(OutputString[i]);}
    Usb_set_tx_ready();
    F_USB_Inp = 0; InputByte_nn = 0;        // buffer copied show must go on
    SendRS232('>');
     if (i==32) end_point1_ready= 2; else end_point1_ready= 1;
 }
}
unsigned char Cls_input(unsigned char idata *ppp,unsigned char iii)
{unsigned char i,sss;
  sss = 0;
  for ( i = 1; i < iii; i++)
  {  sss += ppp[i]; }
  return sss;
}
void FillInputString_ch (unsigned char ddd)
{     if (F_USB_Inp != 0) { return;}  //
      switch (InputByte_nn )
      { case 0:
         if(ddd == ':')
               { InputByte_nn ++; InputString[0]=':';}
         break;
        case 1:
         if((ddd & 0x01F) <= 16 )      //InputString_Ch
               { InputString[InputByte_nn] = ddd; InputByte_nn ++;}
         else
               {F_USB_Inp = 0x31; }
         break;
         default:
             InputString[InputByte_nn] = ddd; InputByte_nn ++;
             if(InputByte_nn >= ((InputString[1] & 0x01F)+ 7))      //InputString_Ch
             {if (ddd == 0x0D)
                   { if (Cls_input(&InputString,InputByte_nn) == 0)
                      {F_USB_Inp = 0xFF; InputString[InputByte_nn] = ddd;} //OK
                     else  {
                      F_USB_Inp = 0xFF; InputString[InputByte_nn] = 0x0D; //test
                      //F_USB_Inp = 0x32;
                      } //ERROR CLS
                   }
                else                  {F_USB_Inp = 0x33;   } //ERROR 0x0D
               }
         break;
      }

}
void ProcessUsbComand(void)
{ unsigned char i,e;
  for (i=0; i <= ((InputString[1] & 0x1F)+6);i++)  {Put_char_Asci(InputString[i],'<'); }
          Put_char_Asci(F_USB_Inp,'+');  //TEST PRINT

  if (F_USB_Inp == 0xFF)
  { F_USB_Inp = 0x34;            //unknown comand
    if (InputString[4] == 0x30 )
     { XM_Adr  =   (InputString[2] & 0x07)*256 + InputString[3];    //write
       i = 0;
       while ( i < (InputString[1] & 0x1F) )
           { ACC = InputString[i+5]; Write_EPROM_char (); i++;} //maybe zero data
       PROG_WAIT_EPROM();                                       //
     }   //write finished
    if ((InputString[4] == 0x30 )||(InputString[4] == 0x31 ))
     { //read EPROM
       OutputString[0] = ':';
       OutputString[1] = InputString[1];   //Len
       OutputString[2] = InputString[2];
       OutputString[3] = InputString[3];
       OutputString[4] = 0x32;             //Answer
       XM_Adr  =   (InputString[2]& 0x07)*256 + InputString[3];
       i=0;
       while ( i < (InputString[1] & 0x1F) )
       { OutputString[i+5] = Read_EPROM_char (); i++;} //data string
       OutputString[i+5] = 'F'; i++; //Cls_input(&OutputString, i);
       OutputString[i+5] = 0x0D;
       F_Output = 1;
       F_USB_Inp = 0xFF;
     }  //read finished
  }     //only 2 comands
   //ERROR
  if ( F_USB_Inp != 0xFF )  //ERROR
     { 
       OutputString[0] = ':';
       OutputString[1] = 'A';  //0x01;
       OutputString[2] = '0';  //0x00;
       OutputString[3] = '0';  //0x00;
       OutputString[4] = '3';  //0x33;
       OutputString[5] = F_USB_Inp; //F_USB_Inp;
       OutputString[6] = 'F';  //Cls_input(&OutputString, 6);
       OutputString[7] = 0x0D; F_Output = 1;
     }
  for (i = 0; i <= ((OutputString[1] & 0x1F)+6); i++)
     {Put_char_Asci(OutputString[i],'>'); }
  Put_char_Asci((OutputString[1] & 0x1F),'*');  //TEST PRINT
}
main()
{
 /* �믮����� ���樠������ USB */
// UsbInit();
  LEDCON = 0xAA;
 PGM1 = 0;
 PGM2 = 0;
 /* ���䨣��஢���� RS232 (��� �⫠���) */
// SCON    = MSK_UART_8BIT;
// CKCON0 |= MSK_X2;
// PCON   |= MSK_SMOD1;
// BDRCON |= 2;
// BDRCON |= 0x1C;
// BDRCON &= ~1;
// BRL     = 100;
// SCON   |= MSK_UART_ENABLE_RX|MSK_UART_TX_READY;
/*;    x     x     x   PS     PT1   PX1  PT0  PX0   X0 -TxC CLOCK       */
/*;    0     0     0   0      0     0    1    0                         */
//    IP = 0;
/*;  GATE1   C/T   M1   M0  GATE0   C/T   M1   M0                       */
/*;    0     0     1     0    0     0     1    0                        */
/*;        Timer1  reload for SERial        TL0 =T0 TH0 =T1             */
    TMOD=0x22;                /*  */
/*;   TF1    TR1   TF0 TR0   IE1   IT1  IE0  IT0       TCON             */
/*;    0     1     0   1      0     1    0    0                         */
/*;    0     1     0   0      0     1    0    1   & 55 = 55             */
    TCON=0x11;

/*;  SM0    SM1   SM2  REN  TB8     RB8  TI  RI       SCON               */
/*;    0     1     1   1      0     0    1    1                          */
/*;    1     1     1   1                         0xF8 - MASK WDOG =0x70  */
    SCON=0x73;
    PCON=0x80;
/*;   TF2   EXF2 RCLK TCLK  EXEN2  TR2  C/T2 CP/RL       T2CON             */
/*;    0     0     1   1      0     1    0    0                         */
/*;    0     0     1   1      0     1    1    1   & 37 = 34             */
    T2CON = 0x34; //RCLK = 1; TCLK = 1 TIMER2->BAUD RATE
/*;   DPU    --    M0  --    XRS1  XRS0 EXTRAM A0       AUXR             */
/*;    0     X     0   X      1     1      0    0                         */
/*;    0     X     0   X      1     1      0    0   RESET VALUE           */
/*;    0     X     0   X      1     1      0    0   TEST  VALUE                   */
    TH2=0xFF; TL2=0;
    RCAP2H = 0xFF; RCAP2L = 0xB2;  //24000000/32/9600 =78.125 00B2  = 256 - 78
/*-----------------28.06.95 14:59-------------------
 EA -  ET2 ES ET1 EX1 ET0 EX0
  1  0  0   0   0   0   1  0        = 0X88
--------------------------------------------------*/
       IE = 0x82;
       TH0 = 48;       //24000000/12/9600   256-208 = 48
       LEDCON = 0xAA;
       TI = 0;
       SBUF = 0x20;
       Timeout_USB  = 5;
 /* �᭮���� 横� �ணࠬ�� */
//code char ccc[44]   = {":10000000000102030405060708090A0B0C0D0E0F78\xD"};
F_USB_Inp = 0;  //
InputByte_nn = 0;
/*
while ( 1 )
{
 for ( ttt = 0;ttt <= 22; ttt++ )
 {  d = ccc[ttt];
    FillInputString_ch(d);
   if( F_USB_Inp != 0)
       {ProcessUsbComand();
         F_USB_Inp = 0; InputByte_nn = 0;
       }
 }
}
  */
for ( ttt = 0;ttt < 10;ttt++ )
{
while(!TI){}
 TI = 0; SBUF = xxx[ttt];
}
print_descriptor();
 /* �믮����� ���樠������ USB */
 usb_init();
 SendRS232('I');

 /* �믮����� ���樠������ CDC */
 cdc_init();
 /* ���ன�⢮ ������祭� � 設� */
 usb_connected = FALSE;
  SendRS232('C');
while ( 1 )
 {
    main_task();
   if( F_USB_Inp != 0)
          {ProcessUsbComand();
           // F_USB_Inp =0; InputByte_nn = 0;
          }
   if (Timeout_USB  == 0)
       { Timeout_USB  = 50; F_USB_Inp =0; InputByte_nn = 0;}
  /* �᫨ ���ன�⢮ �⪫�祭� �� 設� */
  if (!usb_connected)
  {
    /* �᫨ ����祭 ᨣ��� ���㤪� */
    if (Usb_resume())
    {
      /* ��⠭����� 䫠� ��⨢���� */
      usb_connected = TRUE;
      /* ��� ०��� SUSPEND */
      Usb_clear_suspend_clock();
      Usb_clear_suspend();
      Usb_clear_resume();
      Usb_clear_sof();
      SendRS232('C');
    }
  /* �᫨ ���ன�⢮ ������祭� � 設� */
  } else {
   /* �᫨ ����祭 ᨣ��� "���믠���" */
   if (Usb_suspend())
   {
     usb_connected = FALSE;
     Usb_clear_suspend();
     Usb_set_suspend_clock();
     SendRS232('U');
   }

   /* �᫨ ����祭 ᨣ��� ��� */
   if (Usb_reset())
   {
     Usb_clear_reset();
     SendRS232('R');
   }

   /* ᨣ��� SOF */
   if (Usb_sof())
   {
    Usb_clear_sof();
    //SendRS232('S');
   }

   /* �����㦥�� ���뢠��� �� ����筮� �窨 */
   if (Usb_endpoint_interrupt())
   {
    /* ��४������� �� 0 ������� ��� */
    Usb_select_ep(0);
    //SendRS232('0');
    /* �᫨ ����祭 ����� SETUP */
    if (Usb_setup_received())
    {  SendRS232('X');
     /* ��ࠡ�⪠ ����� setup */
     UsbControlPacketProcessed();
    }
    /* ��४������� �� 1 ������� ��� */
    Usb_select_ep(1);
    switch (end_point1_ready)
    {
     case 1:
     {
       if (Usb_tx_complete())
       {
        Usb_clear_tx_complete();
        Usb_set_tx_ready();
        end_point1_ready = 2;
       }
       break;
     }
     case 2:
     {
       if (Usb_tx_complete()) // Waiting for send data
       {  if (F_Output)
         { Usb_clear_tx_complete(); F_Output = 0;
           end_point1_ready = 0;
         }
       }
       break;
     default:
       break;
     }
    }

    /* ��४������� �� 3 ������� ��� */

    Usb_select_ep(3);
    if (Usb_tx_complete())
    {
      Usb_clear_tx_complete();
    }

    /* ����祭�� ������ � 2 ����筮� �窨 */
    /* BULK OUT */
    Usb_select_ep(2);
    bcount = UBYCTLX;
    if (bcount > 0)
    {
     for (i=0; i < bcount;i++)
     { d = Usb_read_byte();  Timeout_USB  = 50; /* 500 ms */
       FillInputString_ch(d);
     }
      Usb_clear_rx();
    }
    // Usb_clear_rx();

   } /* end if interrupt */

  } /* end if connected */

  /* �������� ��⨢���� �ਫ������ */
  PGM1 = p_test; p_test=!p_test;

 } /* end for ;; */
}