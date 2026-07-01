/* Routine = ACCEPT_NUMERIC.C
 * Version = 1.04
 * Dated  = 2024/03/13
 * Author = Chuck H.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <math.h>
#include <inttypes.h>


#define COB_KEYWORD_INLINE __inline
#include <libcob.h>

#if defined (HAVE_NCURSESW_NCURSES_H)
#include <ncursesw/ncurses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_NCURSESW_CURSES_H)
#include <ncursesw/curses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_NCURSES_H)
#include <ncurses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_NCURSES_NCURSES_H)
#include <ncurses/ncurses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_PDCURSES_H)
#define PDC_NCMOUSE   /* use ncurses compatible mouse API */
#include <pdcurses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_PDCURSES_CURSES_H)
#define PDC_NCMOUSE   /* use ncurses compatible mouse API */
#include <pdcurses/curses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_XCURSES_H)
#define PDC_NCMOUSE   /* use ncurses compatible mouse API */
#include <xcurses.h>
#define WITH_EXTENDED_SCREENIO
#elif defined (HAVE_XCURSES_CURSES_H)
#include <xcurses/curses.h>
#define WITH_EXTENDED_SCREENIO
#else
#include <curses.h>
#endif

#include <time.h>

#define TRUE   1
#define FALSE  0
   typedef int MYBOOL;

#define IS_VALID_DIGIT_DATA(c)  (c >= '0' && c <= '9')  /* valid digits '0' - '9' */
#define COB_STORE_CHECK_SIGN_DROP (1 << 16)

#define A_ATTR  (A_ATTRIBUTES ^ A_COLOR)

#define MYKEY_BACKSPACE     0x00000008
#define MYKEY_ESCAPE        0x0000001B
#define MYKEY_ENTER         0x0000000D
#define MYKEY_TAB           0x00000009
#define MYKEY_BACK_TAB      0x0000015F

       /************************************************************/
       /*                                                          */
       /*  the follow keys are not defined in ncurses.h            */
       /*  so we need to manually define them.                     */
       /*                                                          */
       /************************************************************/

#ifndef PDCURSES
#define PADENTER            0x0000000D
#define PADPLUS             0x0000002B
#define PADMINUS            0x0000002D
#define CTL_LEFT            0x00000228
#define CTL_RIGHT           0x00000237
#endif

       /************************************************************/
       /*                                                          */
       /*  copied from coblocal.h as it                            */
       /*  is not in the distribution libraries.                   */
       /*                                                          */
       /************************************************************/

/* Field/attribute initializers */
#define COB_FIELD_INIT_F(field,x,y,z) do { \
  field.size = x; \
  field.data = y; \
  field.attr = z; \
  } ONCE_COB
#define COB_FIELD_INIT(x,y,z) \
  COB_FIELD_INIT_F(field,x,y,z)

#define COB_ATTR_INIT_A(attr,u,v,x,y,z) do { \
  attr.type = u; \
  attr.digits = v; \
  attr.scale = x; \
  attr.flags = y; \
  attr.pic = z; \
  } ONCE_COB
#define COB_ATTR_INIT(u,v,x,y,z) \
  COB_ATTR_INIT_A(attr,u,v,x,y,z)


   typedef struct _COMM_AREA
   {
       short               line;
       short               column;
       short               mode;
       short               fg;
       short               bg;
       short               fg2;
       short               return_code;
       short               error_code;
   }COMM_AREA,  *PCOMM_AREA;



COB_EXT_EXPORT int ACCEPT_NUMERIC(void *a, void *b);

void       DUMP_HEX(void *source, int length);
void       START_TIME();
void       END_TIME();
int        cob_accept_numeric(cob_field *a,
                              cob_field *comm);
int        cob_classic_edit_numeric(cob_field *f,
                                    cob_field *g,
                                    int       have_bin_notrunc,
                                    int       row,
                                    int       col,
                                    int       digits_left,
                                    int       digits_right,
                                    PCOMM_AREA    ptr_comm,
                                    chtype *bigchar_array);
void       addchar(unsigned char *buff,
                   unsigned char *ptr_char,
                   int ch);
void       insert_digit(unsigned char *ptr_home,
                        unsigned char *ptr_pos,
                        unsigned char *ptr_decimal,
                        unsigned char *ptr_end,
                        int           ch);
void       put_classic_field(int row,
                             int col,
                             unsigned char *ptr_home,
                             unsigned char *ptr_pos,
                             int len,
                             int insert_mode,
                             chtype *bigchar_array);
void       put_field(int row,
                     int col,
                     int col_end,
                     unsigned char *buff,
                     int len,
                     int *cntr_left,
                     chtype *bigchar_array);
void       delete_classic_char(unsigned char *ptr_home,
                               unsigned char *ptr_decimal,
                               unsigned char *ptr_end,
                               unsigned char *ptr_pos,
                               int           ch);
void       deletechar(unsigned char *buff,
                      unsigned char *ptr_end,
                      int ch);
void  sound_bell();
int        check_for_overflow(cob_field *f,
                              unsigned char *buff,
                              int cntr_left,
                              char fld_sign);
void       get_field(cob_field *f,
                     cob_field *field,
                     int       left_digits,
                     unsigned char decimal_char);
void       set_colors(chtype   *ptr_bigchar_array,
                      int      digits_left,
                      int      digits_right,
                      int      len,
                      int      sign,
                      PCOMM_AREA    ptr_comm);


static clock_t     start_time, end_time, elapsed_time;

   typedef struct _BIN_SIZE
   {
       int           bs_len;
       unsigned char bs_value[20];
   }BIN_SIZE,  *PBIN_SIZE;


          BIN_SIZE    bs_unsigned[] =
   {
       {  3  ,     "255                 " } ,
       {  5  ,     "65535               " } ,
       {  8  ,     "16777215            " } ,
       {  10 ,     "4294967295          " } ,
       {  13 ,     "1099511627775       " } ,
       {  15 ,     "281474976710655     " } ,
       {  17 ,     "72057594037927935   " } ,
       {  20 ,     "18446744073709551615" } };

          BIN_SIZE    bs_positive[] =
   {
       {  3  ,     "127                 " } ,
       {  5  ,     "32767               " } ,
       {  8  ,     "083886075           " } ,
       {  10 ,     "2147483647          " } ,
       {  13 ,     "05497558138875      " } ,
       {  15 ,     "140737488355327     " } ,
       {  17 ,     "36028797018963967   " } ,
       {  20 ,     "09223372036854775807" } } ;


          BIN_SIZE    bs_negative[] =
   {
       {  3  ,     "128                 " } ,
       {  5  ,     "32768               " } ,
       {  8  ,     "08388608            " } ,
       {  10 ,     "2147483648          " } ,
       {  13 ,     "0549755813888       " } ,
       {  15 ,     "140737488355328     " } ,
       {  17 ,     "36028797018963968   " } ,
       {  20 ,     "09223372036854775808" } } ;


int  cob_accept_numeric(cob_field *f,
                        cob_field *comm)
{

   cob_field field;
   cob_field_attr  attr;
   struct __cob_global  *ptr_cob_global;
   cob_module  *ptr_module;

   int max_row, max_col, row, col, col_end, len, len_adj;
   int digits_left, digits_right, digits, scale, sign, ch;
   int cntr_left = 0;
   int cntr_right = 0;
   int have_decimal = 0;
   int have_bin_notrunc = 0;
   int have_classic = 0;
   unsigned char  buff[COB_MAX_BINARY + 2];
   unsigned char  buff2[COB_MAX_BINARY + 2];
   unsigned char  *ptr_char;
   unsigned char  *ptr_char_next;
   unsigned char  *ptr_end;
   unsigned char  *ptr_sign;
   unsigned char  decimal_char, updt_char;
   chtype         bigchar_array[COB_MAX_BINARY + 2];
       /************************************************************/
       /*  blank is not signed                                     */
       /*  +     is positive                                       */
       /*  -     is negative                                       */
       /************************************************************/


   char            fld_sign = ' ';
   PBIN_SIZE       ptr_bs;
   PCOMM_AREA           ptr_comm;
   ptr_comm  = (PCOMM_AREA)comm->data;
   ptr_comm->error_code = 0;
   ptr_comm->return_code = 999;

   if (stdscr == NULL)
   {
       sound_bell();
       ptr_comm->error_code = 4;
       return 4;
   }

   savetty();
   curs_set(1);
   cbreak ();
   keypad (stdscr, 1);
   nonl ();
   noecho ();

   ptr_cob_global = cob_get_global_ptr();
   ptr_module     = ptr_cob_global->cob_current_module;
   decimal_char   = ptr_module->decimal_point;

   getmaxyx(stdscr, max_row, max_col);
   digits = COB_FIELD_DIGITS(f);
   scale  = COB_FIELD_SCALE (f);
   sign = (COB_FIELD_HAVE_SIGN (f)) ? 1 : 0;

   if ((!COB_FIELD_BINARY_TRUNC(f))
   && ( (COB_FIELD_BINARY_SWAP(f))
     || (COB_FIELD_REAL_BINARY(f)) ) )
   {
       ptr_bs = &bs_unsigned[0];
       ptr_bs += (f->size - 1);
       digits  = ptr_bs->bs_len;
       have_bin_notrunc = 1;
   }

   if (scale > 0)
   {
       if (digits > scale)
       {
           digits_left = digits - scale;
           digits_right = scale;
       }
       else
       {
           digits_left = 0;
           digits_right = scale - digits;
       }
   }
   else
   {
       if (scale < 0)
       {
           digits_left = digits + scale;
           digits_right = 0;
       }
       else
       {
           digits_left = digits;
           digits_right = 0;
       }
   }

   row = ptr_comm->line - 1;
   col = ptr_comm->column - 1;

   if ((row < 0) || (row > max_row))
   {
       printf("Starting row outside of screen bounds \n");
       sound_bell();
       ptr_comm->error_code = 8;
       return 8;
   }

   if ((col < 0) || (col > max_col))
   {
       printf("Starting col outside of screen bounds \n");
       sound_bell();
       ptr_comm->error_code = 12;
       return 12;
   }

   len = digits + sign;
   len_adj = len;

       /************************************************************/
       /*  this len accounts for the added decimal point           */
       /************************************************************/

   if (scale > 0)
       len++;

   if (col + len - 1 > max_col)
   {
       printf("Ending col outside of screen bounds \n");
       ptr_comm->error_code = 16;
       sound_bell();
       return 16;
   }

   if (sign)
   {
       COB_FIELD_INIT ((size_t)len_adj, buff, &attr);
       COB_ATTR_INIT (COB_TYPE_NUMERIC_DISPLAY,
                      (unsigned short)(len_adj - 1),
                      COB_FIELD_SCALE(f),
                      (COB_FLAG_HAVE_SIGN | COB_FLAG_SIGN_SEPARATE),
                      NULL);
   }
   else
   {
       COB_FIELD_INIT ((size_t)len_adj, buff, &attr);
       COB_ATTR_INIT (COB_TYPE_NUMERIC_DISPLAY,
                      (unsigned short)(len_adj),
                      COB_FIELD_SCALE(f),
                      0,
                      NULL);
   }

   set_colors(bigchar_array,
              digits_left,
              digits_right,
              len,
              sign,
              ptr_comm);

   if (ptr_comm->mode > 0)
   {
       memset(buff, ' ', COB_MAX_BINARY + 2);
       get_field(f, &field, digits_left, decimal_char);
       return (cob_classic_edit_numeric(f, &field,
                                        have_bin_notrunc,
                                        row, col,
                                        digits_left, digits_right, ptr_comm,
                                        bigchar_array));
   }
   else
   {
       memset(buff, ' ', COB_MAX_BINARY + 2);
       memset(buff2, ' ', COB_MAX_BINARY + 2);
   }

   ptr_sign = buff + len - 1;

   if (sign)
   {
       ptr_end = ptr_sign - 1;
       col_end = col + len - 2;
       *ptr_sign = '+';
   }
   else
   {
       ptr_end = ptr_sign;
       col_end = col + len - 1;
   }

   put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);

   do
   {
       flushinp();
       ch = getch();
//     printf(" getch returned %d\n", ch);

       if ((ch == KEY_ENTER)
       || (ch == PADENTER)
       || (ch == MYKEY_ENTER)
       || (ch == KEY_PPAGE)
       || (ch == KEY_NPAGE)
       || (ch == KEY_BTAB)
       || (ch == MYKEY_TAB)
       || ((ch >= KEY_F(1)) && (ch <= KEY_F(48))))
       {
           if (have_bin_notrunc)
           {
               fld_sign = ' ';
               if (sign)
                   fld_sign = (*ptr_sign == '-' ? '-' : '+');
               if (check_for_overflow(f, buff, cntr_left, fld_sign) )
               {
                   sound_bell();
                   sound_bell();
                   sound_bell();
                   ch = 0;
                   wrefresh(stdscr);
                   continue;
               }
           }
           break;
       }

       if (ch == MYKEY_ESCAPE)
       {
           memcpy(buff, buff2, len + 1);
           cntr_left = digits_left;
           cntr_right = digits_right;
           put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           ptr_comm->return_code = 99;
           return (0);
       }

       if (IS_VALID_DIGIT_DATA(ch))
       {
           if (have_decimal)
           {
               if (cntr_right < digits_right)
                   cntr_right++;
               else
               {
                   sound_bell();
                   wrefresh(stdscr);
                   continue;
               }
           }
           else
           {
               if (cntr_left < digits_left)
                   cntr_left++;
               else
               {
                   sound_bell();
                   wrefresh(stdscr);
                   continue;
               }
           }
           addchar(buff, ptr_end, ch);
           put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           continue;
       }

       if ((ch == '+') || (ch == PADPLUS))
       {
           if (sign)
           {
               *ptr_sign = '+';
               put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           }
           else
           {
               sound_bell();
               wrefresh(stdscr);
           }
           continue;
       }

       if ((ch == '-') || (ch == PADMINUS))
       {
           if (sign)
           {
               *ptr_sign = '-';
               put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           }
           else
           {
               sound_bell();
               wrefresh(stdscr);
           }
           continue;
       }

       if ((ch == decimal_char) && (scale > 0) && (have_decimal == 0))
       {
           have_decimal = 1;
           addchar(buff, ptr_end, ch);
           put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           continue;
       }

       if ((ch == KEY_BACKSPACE) || (ch == MYKEY_BACKSPACE))
       {
           if (*ptr_end == ' ')
           {
               sound_bell();
               wrefresh(stdscr);
               continue;
           }
           if (have_decimal == 0)
               cntr_left--;
           else if (cntr_right == 0)
               have_decimal = 0;
           else
               cntr_right--;
           deletechar(buff, ptr_end, ch);
           put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           continue;
       }

       if (ch == KEY_DC)
       {
           have_decimal = 0;
           cntr_right = 0;
           cntr_left = 0;
           memset(buff, ' ', len);
           put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);
           continue;
       }

       if ((ch == KEY_HOME)
       ||  (ch == KEY_END)
       ||  (ch == KEY_RIGHT)
       ||  (ch == KEY_LEFT))
       {
           have_classic = 1;
           break;
       }

       sound_bell();
       wrefresh(stdscr);
   }
   while (1);

       /************************************************************/
       /*  first check for missing decimal point                   */
       /************************************************************/

   if ((scale > 0) && (have_decimal == 0))
   {
       have_decimal = 1;
       ch = '.';
       addchar(buff, ptr_end, ch);
   }

       /************************************************************/
       /*  add trailing zeros if needed                            */
       /************************************************************/

   while (cntr_right < digits_right)
   {
       ch = '0';
       addchar(buff, ptr_end, ch);
       cntr_right++;
   }

       /************************************************************/
       /*  add leading zeros if needed                             */
       /************************************************************/

   ptr_char = buff;

   for(; ptr_char < ptr_end; ptr_char++)
   {
       if (*ptr_char == ' ')
           *ptr_char = '0';
       else
           break;
   }

   if (have_classic)
       return (cob_classic_edit_numeric(f, &field,
                                        have_bin_notrunc,
                                        row, col,
                                        digits_left, digits_right, ptr_comm,
                                        bigchar_array));

   put_field(row, col, col_end, buff, len, &cntr_left, bigchar_array);

       /************************************************************/
       /*  remove decimal point if present                         */
       /************************************************************/

   if (have_decimal)
   {
       ptr_char = buff + digits_left;
       if ((*ptr_char == decimal_char) && (ptr_char <= ptr_sign))
       {
           ptr_char_next = ptr_char + 1;
           while(ptr_char_next <= ptr_sign)
           {
               *ptr_char = *ptr_char_next;
               ptr_char++;
               ptr_char_next++;
           }
       len--;
       }
   }

   if ((ch == KEY_ENTER)
   || (ch == PADENTER)
   || (ch == MYKEY_ENTER))
       ptr_comm->return_code = 0;
   else if (ch == KEY_PPAGE)
       ptr_comm->return_code = 49;
   else if (ch == KEY_NPAGE)
       ptr_comm->return_code = 50;
   else if (ch == MYKEY_TAB)
       ptr_comm->return_code = 51;
   else if (ch == KEY_BTAB)
       ptr_comm->return_code = 52;
   else if  ((ch >= KEY_F(1)) && (ch <= KEY_F(48)))
       ptr_comm->return_code = (ch - KEY_F0);

   cob_move (&field, f);
   resetty();
   return(0);

}


int cob_classic_edit_numeric(cob_field *f,
                             cob_field *g,
                             int       have_bin_notrunc,
                             int       row,
                             int       col,
                             int       digits_left,
                             int       digits_right,
                             PCOMM_AREA    ptr_comm,
                             chtype    *bigchar_array)
{
   unsigned char   buff2[COB_MAX_BINARY + 2];
   unsigned char   fld_sign, decimal_char;
   unsigned char   *ptr_home,
                   *ptr_end,
                   *ptr_dec_p1,
                   *ptr_decimal,
                   *ptr_sign,
                   *ptr_char,
                   *ptr_next,
                   *ptr_done,
                   *ptr_pos;
   int             scale, sign, len, ch;
   int             insert_mode = 0;

   scale  = COB_FIELD_SCALE (g);
   sign = (COB_FIELD_HAVE_SIGN (g)) ? 1 : 0;
   ptr_home = g->data;

   if (scale > 0)
   {
       len          = g->size + 1;
       ptr_decimal  = ptr_home + digits_left;
       decimal_char = *ptr_decimal;
       ptr_dec_p1   = ptr_decimal - 1;
       if (sign)
       {
           ptr_sign = ptr_home + g->size;
           ptr_end  = ptr_sign - 1;
       }
       else
           ptr_end  = ptr_home + g->size - 1;
   }
   else
   {
       len          = g->size;
       ptr_decimal  = NULL;
       ptr_dec_p1   = NULL;
       if (sign)
       {
           ptr_sign = ptr_home + g->size - 1;
           ptr_end  = ptr_sign - 1;
       }
       else
           ptr_end  = ptr_home + g->size - 1;
   }

   if (ptr_decimal)
       ptr_pos     = ptr_dec_p1;
   else
       ptr_pos     = ptr_end;

   memcpy(buff2, ptr_home, len);

   put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);

   do
   {
       flushinp();
       ch = getch();
//     printf(" getch returned %d\n", ch);

       if ((ch == KEY_ENTER)
       || (ch == PADENTER)
       || (ch == MYKEY_ENTER)
       || (ch == KEY_PPAGE)
       || (ch == KEY_NPAGE)
       || (ch == KEY_BTAB)
       || (ch == MYKEY_TAB)
       || ((ch >= KEY_F(1)) && (ch <= KEY_F(48))))
       {
           if (have_bin_notrunc)
           {
               fld_sign = ' ';
               if (sign)
                   fld_sign = (*ptr_sign == '-' ? '-' : '+');
               if (check_for_overflow(f, ptr_home, digits_left, fld_sign) )
               {
                   sound_bell();
                   sound_bell();
                   sound_bell();
                   ch = 0;
                   wrefresh(stdscr);
                   continue;
               }
           }
           break;
       }

       if (ch == MYKEY_ESCAPE)
       {
           memcpy(ptr_home, buff2, len);
           ptr_pos = ptr_end;
           put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
           ptr_comm->return_code = 99;
           return (1);
       }

       if (ch == KEY_IC)
       {
           insert_mode = (insert_mode) ? 0 : 1;
           if (insert_mode)
           {
               curs_set(2);
           }
           else
           {
               curs_set(1);
           }
           put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
           continue;
       }

       if ((ch == KEY_LEFT) && (ptr_pos > ptr_home))
       {
           ptr_pos--;
           wmove(stdscr, row, col + (ptr_pos - ptr_home));
           wrefresh(stdscr);
           continue;
       }

       if ((ch == KEY_RIGHT) && (ptr_pos <  ptr_end))
       {
           ptr_pos++;
           wmove(stdscr, row, col + (ptr_pos - ptr_home));
           wrefresh(stdscr);
           continue;
       }

       if (ch == KEY_HOME)
       {
           ptr_pos  = ptr_home;
           wmove(stdscr, row, col);
           wrefresh(stdscr);
           continue;
       }

       if (ch == KEY_END)
       {
           ptr_pos  = ptr_end;
           wmove(stdscr, row, col + (ptr_end - ptr_home));
           wrefresh(stdscr);
           continue;
       }

       if (IS_VALID_DIGIT_DATA(ch))
       {
           if (ptr_pos == ptr_decimal)
           {
               sound_bell();
               wrefresh(stdscr);
               continue;
           }
           if (insert_mode)
           {
               insert_digit(ptr_home, ptr_pos, ptr_decimal, ptr_end, ch);
           }
           else
           {
               *ptr_pos = (char)ch;
               if (ptr_decimal)
               {
                   if ((ptr_pos != ptr_decimal) && (ptr_pos < ptr_end))
                       ptr_pos++;
               }
               else
               {
                   if (ptr_pos < ptr_end)
                       ptr_pos++;
               }
           }
           put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
           continue;
       }

       if ((ch == '+') || (ch == PADPLUS))
       {
           if (sign)
           {
               *ptr_sign = '+';
               put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
           }
           else
           {
               sound_bell();
               wrefresh(stdscr);
           }
           continue;
       }

       if ((ch == '-') || (ch == PADMINUS))
       {
           if (sign)
           {
               *ptr_sign = '-';
               put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
           }
           else
           {
               sound_bell();
               wrefresh(stdscr);
           }
           continue;
       }

       if (ptr_decimal)
       {
           if (ch == decimal_char)
           {
#ifdef DECIMAL_RIGHT
               ptr_pos  = ptr_decimal + 1;
#else
               ptr_pos  = ptr_dec_p1;
#endif
               wmove(stdscr, row, col + (ptr_pos - ptr_home));
               wrefresh(stdscr);
               continue;
           }
           else if (ch == CTL_LEFT)
           {
               ptr_pos  = ptr_dec_p1;
               wmove(stdscr, row, col + (ptr_pos - ptr_home));
               wrefresh(stdscr);
               continue;
           }
           else if (ch == CTL_RIGHT)
           {
               ptr_pos  = ptr_decimal + 1;
               wmove(stdscr, row, col + (ptr_pos - ptr_home));
               wrefresh(stdscr);
               continue;
           }
       }

       if ((ch == KEY_BACKSPACE) || (ch == KEY_DC) ||(ch == MYKEY_BACKSPACE))
       {
           delete_classic_char(ptr_home, ptr_decimal, ptr_end, ptr_pos, ch);
           put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
           continue;
       }

       sound_bell();
       wrefresh(stdscr);
   }
   while (1);

   put_classic_field(row, col, ptr_home, ptr_pos, len, insert_mode, bigchar_array);
       /************************************************************/
       /*  remove decimal point if present                         */
       /************************************************************/

   if (ptr_decimal)
   {
       ptr_char = ptr_decimal;
       ptr_next = ptr_char + 1;
       if (sign)
           ptr_done = ptr_sign;
       else
           ptr_done = ptr_end;
       while(ptr_next <= ptr_done)
       {
           *ptr_char = *ptr_next;
           ptr_char++;
           ptr_next++;
       }
       len--;
   }

   if ((ch == KEY_ENTER)
   || (ch == PADENTER)
   || (ch == MYKEY_ENTER))
       ptr_comm->return_code = 0;
   else if (ch == KEY_PPAGE)
       ptr_comm->return_code = 49;
   else if (ch == KEY_NPAGE)
       ptr_comm->return_code = 50;
   else if (ch == MYKEY_TAB)
       ptr_comm->return_code = 51;
   else if (ch == KEY_BTAB)
       ptr_comm->return_code = 52;
   else if  ((ch >= KEY_F(1)) && (ch <= KEY_F(48)))
       ptr_comm->return_code = (ch - KEY_F0);

   cob_move (g, f);
   resetty();
   return(0);

}


       /************************************************************/
       /*                                                          */
       /*  this function will move the input field to a display    */
       /*  numeric field with trailing sign separate.              */
       /*                                                          */
       /*  then it will check to see if a decimal point is         */
       /*  needed, if so then it will insert the decimal point     */
       /*  after the left digits.                                  */
       /*                                                          */
       /************************************************************/

void get_field(cob_field *f,
               cob_field *field,
               int       left_digits,
               unsigned char decimal_char)
{
   unsigned char  *ptr_char, *ptr_char_next, *ptr_decimal;
   int scale  = COB_FIELD_SCALE (field);
   cob_move (f, field);

   if (scale <= 0)
       return;

   ptr_decimal = field->data + left_digits;
   ptr_char_next = field->data + field->size;
   ptr_char = ptr_char_next - 1;

   for(; ptr_char >= ptr_decimal; ptr_char--, ptr_char_next--)
   {
       *ptr_char_next = *ptr_char;
   }

   *ptr_decimal = decimal_char;
   return;
}


int   check_for_overflow(cob_field *f,
                         unsigned char *buff,
                         int cntr_left,
                         char fld_sign)
{
   PBIN_SIZE       ptr_bs;
   int             ret;

   switch (fld_sign)
   {
       case ' ' :
           ptr_bs = &bs_unsigned[0];
           break;
       case '+' :
           ptr_bs = &bs_positive[0];
           break;
       case '-' :
           ptr_bs = &bs_negative[0];
           break;
   }

       ptr_bs += (f->size - 1);
       ret = memcmp(ptr_bs->bs_value, buff, ptr_bs->bs_len);

       if (ret < 0)
           return 1;
       else
           return 0;
}


void  sound_bell()
{
       cob_sys_sound_bell();
#ifndef __WIN32
       flash();
#endif

   wrefresh(stdscr);
   return;
}


void       put_classic_field(int row,
                             int col,
                             unsigned char *ptr_home,
                             unsigned char *ptr_pos,
                             int len,
                             int insert_mode,
                             chtype *bigchar_array)
{
   int cntr, rtn;
   unsigned char   *ptr_char;
   chtype          *ptr_big;

   wmove(stdscr, row, col + (ptr_pos - ptr_home));

   ptr_char = ptr_home;
   ptr_big  = bigchar_array;

   if (insert_mode)
   {
       for(cntr = 0; cntr < len; ptr_char++, ptr_big++, cntr++)
       {
           *ptr_big  &= A_COLOR;
           *ptr_big  |= *ptr_char;
           *ptr_big  |= A_REVERSE;
       }
   }
   else
   {
       for(cntr = 0; cntr < len; ptr_char++, ptr_big++, cntr++)
       {
           *ptr_big  &= A_COLOR;
           *ptr_big  |= *ptr_char;
       }
   }

   rtn = mvwaddchnstr(stdscr, row, col, bigchar_array, len);
   if (rtn != 0)
   {
       printf("Write to stdscr failed with %d \n", rtn);
       exit(12);
   }
   wmove(stdscr, row, col + (ptr_pos -ptr_home));
   wrefresh(stdscr);
   return;
}


void put_field(int row,
               int col,
               int col_end,
               unsigned char *buff,
               int len,
               int *cntr_left,
               chtype *bigchar_array)
{
   int rtn, cntr, limit;
   unsigned char   *ptr_char;
   chtype          *ptr_big;

   ptr_char = buff;
   limit    = col_end - col;

   for(cntr = 0; cntr < limit;
           cntr++, ptr_char++)
   {
       if ((*ptr_char != '0') && (*ptr_char != ' '))
           break;
       if ((*ptr_char == '0') && (IS_VALID_DIGIT_DATA(*(ptr_char + 1))))
       {
           *ptr_char = ' ';
           (*cntr_left)--;
       }
   }

   ptr_char = buff;
   ptr_big  = bigchar_array;

   for(cntr = 0; cntr < len; ptr_char++, ptr_big++, cntr++)
   {
       *ptr_big  &= A_COLOR;
       *ptr_big  |= *ptr_char;
   }
   rtn = mvwaddchnstr(stdscr, row, col, bigchar_array, len);
   if (rtn != 0)
   {
       printf("Write to stdscr failed with %d \n", rtn);
       exit(12);
   }
   wmove(stdscr, row, col_end);
   wrefresh(stdscr);
   return;
}


void  insert_digit(unsigned char *ptr_home,
                   unsigned char *ptr_pos,
                   unsigned char *ptr_decimal,
                   unsigned char *ptr_end,
                   int           ch)
{
   unsigned char    *ptr_char, *ptr_prev, *ptr_next;

   if ((ptr_decimal == NULL) || (ptr_pos < ptr_decimal))
   {
       ptr_char = ptr_home + 1;
       ptr_prev = ptr_home;

       for(;ptr_char <= ptr_pos; ptr_char++, ptr_prev++)
       {
           *ptr_prev = *ptr_char;
       }

       *ptr_prev = (char)ch;
       return;
   }
   else
   {
       ptr_next = ptr_end;
       ptr_char = ptr_end - 1;

       for(;ptr_char >= ptr_pos; ptr_char--, ptr_next--)
       {
           *ptr_next = *ptr_char;
       }

       *ptr_pos  = (char)ch;
       return;
   }
}


void  addchar(unsigned char *ptr_buff, unsigned char *ptr_char, int ch)
{
   if (*ptr_buff != ' ')
   {
       sound_bell();
       return;
   }

   while (ptr_buff < ptr_char)
   {
       *ptr_buff = *(ptr_buff + 1);
       ptr_buff++;
   }

   *ptr_char = (char)ch;

}


void delete_classic_char(unsigned char *ptr_home,
                         unsigned char *ptr_decimal,
                         unsigned char *ptr_end,
                         unsigned char *ptr_pos,
                         int           ch)
{
   unsigned char    *ptr_char, *ptr_prev, *ptr_next;

       /************************************************************/
       /*  first check for remove char left of decimal point. if   */
       /*  true then move to the right.                            */
       /************************************************************/

   if ((ptr_decimal == NULL) || (ptr_pos < ptr_decimal))
   {
       if (ch == KEY_DC)
           ptr_char = ptr_pos;
       else
           ptr_char = ptr_pos - 1;
       ptr_prev = ptr_char - 1;
       for(;ptr_char > ptr_home; ptr_char--, ptr_prev--)
       {
           *ptr_char = *ptr_prev;
       }
       *ptr_char = '0';
       return;
   }

       /************************************************************/
       /*  next check for remove char right of decimal point. if   */
       /*  true then move to the left.                             */
       /************************************************************/

   if (ch == KEY_DC)
       ptr_char = ptr_pos;
   else
   {
       sound_bell();
       wrefresh(stdscr);
       return;
   }
   ptr_next = ptr_char + 1;
   for(;ptr_char < ptr_end; ptr_char++, ptr_next++)
   {
       *ptr_char = *ptr_next;
   }
   *ptr_char = '0';
   return;
}


void deletechar(unsigned char *buff,
                unsigned char *ptr_end,
                int ch)
{
   unsigned char  *ptr_char, *ptr_prev_char;
   ptr_char      = ptr_end;
   ptr_prev_char = ptr_end - 1;

   while ((ptr_prev_char >= buff) && (*ptr_char != ' '))
   {
       *ptr_char = *ptr_prev_char;
       ptr_char--;
       ptr_prev_char--;
   };

   *buff = ' ';
   return;
}


void set_colors(chtype   *ptr_bigchar_array,
                int      digits_left,
                int      digits_right,
                int      len,
                int      sign,
                PCOMM_AREA    ptr_comm)
{
   chtype         bigchar_background;
   chtype         *ptr_bigchar;
   chtype         *ptr_bigchar_end;
   chtype         *ptr_bigchar_left;
   chtype         *ptr_bigchar_right;
   int            row, col, rtn, alt_color, int_pair;
   int            cntr, cntr_grp;
   int            grp_left, grp_right, first_grp;
   int            bkgd_color_pair;
   int            bkgd_fg;
   int            bkgd_bg;
   int            fg, fg2, bg;
   int            alt_pair, reg_pair;
   row = ptr_comm->line - 1;
   col = ptr_comm->column - 1;

   bigchar_background = getbkgd(stdscr);
   bkgd_color_pair = PAIR_NUMBER(bigchar_background);
   rtn = extended_pair_content(bkgd_color_pair, &bkgd_fg, &bkgd_bg);

   if ((ptr_comm->fg < 0) || (ptr_comm->fg > 7))
   {
       fg = bkgd_fg;
   }
   else
   {
       switch (ptr_comm->fg)
       {
           case 0: fg = COLOR_BLACK    ; break;
           case 1: fg = COLOR_BLUE     ; break;
           case 2: fg = COLOR_GREEN    ; break;
           case 3: fg = COLOR_CYAN     ; break;
           case 4: fg = COLOR_RED      ; break;
           case 5: fg = COLOR_MAGENTA  ; break;
           case 6: fg = COLOR_YELLOW   ; break;
           case 7: fg = COLOR_WHITE    ; break;
       }
   }

   if ((ptr_comm->bg < 0) || (ptr_comm->bg > 7))
   {
       bg = bkgd_bg;
   }
   else
   {
       switch (ptr_comm->bg)
       {
           case 0: bg = COLOR_BLACK    ; break;
           case 1: bg = COLOR_BLUE     ; break;
           case 2: bg = COLOR_GREEN    ; break;
           case 3: bg = COLOR_CYAN     ; break;
           case 4: bg = COLOR_RED      ; break;
           case 5: bg = COLOR_MAGENTA  ; break;
           case 6: bg = COLOR_YELLOW   ; break;
           case 7: bg = COLOR_WHITE    ; break;
       }
   }

   switch (ptr_comm->fg2 & 0x07)
   {
       case 0: fg2 = COLOR_BLACK    ; break;
       case 1: fg2 = COLOR_BLUE     ; break;
       case 2: fg2 = COLOR_GREEN    ; break;
       case 3: fg2 = COLOR_CYAN     ; break;
       case 4: fg2 = COLOR_RED      ; break;
       case 5: fg2 = COLOR_MAGENTA  ; break;
       case 6: fg2 = COLOR_YELLOW   ; break;
       case 7: fg2 = COLOR_WHITE    ; break;
   }

   int_pair = find_pair(fg, bg);
   int_pair = alloc_pair(fg, bg);
   reg_pair = int_pair;

   int_pair = find_pair(fg2, bg);
   int_pair = alloc_pair(fg2, bg);
   alt_pair = int_pair;

       /************************************************************/
       /*                                                          */
       /*  first we colorize the digits to the left of the         */
       /*  decimal point                                           */
       /*                                                          */
       /************************************************************/

   grp_left  = digits_left / 3;
   first_grp = digits_left % 3;

   if (grp_left & 0x01)
   {
       if (first_grp > 0)
           alt_color = 0;
       else
           alt_color = 1;
   }
   else
   {
       if (first_grp > 0)
           alt_color = 1;
       else
           alt_color = 0;
   }

   ptr_bigchar = ptr_bigchar_array;

   if ((first_grp) && (digits_left))
   {
       for(cntr = 0; cntr < first_grp; cntr++, ptr_bigchar++)
       {
           if (alt_color)
               *ptr_bigchar = COLOR_PAIR(alt_pair);
           else
               *ptr_bigchar = COLOR_PAIR(reg_pair);
#ifdef DEBUG
           printf(" digit BEFORE  => %#018"PRIx64"\n", *ptr_bigchar);
#endif
       }
       alt_color = (alt_color) ? 0 : 1;
   }

   if ((grp_left) && (digits_left))
   {
       for(cntr_grp = 0; cntr_grp < grp_left; cntr_grp++)
       {
           for(cntr = 0; cntr < 3; cntr++, ptr_bigchar++)
           {
               if (alt_color)
                   *ptr_bigchar = COLOR_PAIR(alt_pair);
               else
                   *ptr_bigchar = COLOR_PAIR(reg_pair);
#ifdef DEBUG
           printf(" digit BEFORE  => %#018"PRIx64"\n", *ptr_bigchar);
#endif
           }
           alt_color = (alt_color) ? 0 : 1;
       }
   }

       /************************************************************/
       /*                                                          */
       /*  next we colorize the digits to the right of the         */
       /*  decimal point                                           */
       /*                                                          */
       /************************************************************/

   alt_color = 1;

   if (digits_right)
   {
       *ptr_bigchar = COLOR_PAIR(reg_pair);
       ptr_bigchar++;
       cntr_grp = 0;
       for(cntr = 0; cntr < digits_right; cntr++,cntr_grp++, ptr_bigchar++)
       {
           if (cntr_grp > 2)
           {
               cntr_grp = 0;
               alt_color = (alt_color) ? 0 : 1;
           }
           if (alt_color)
               *ptr_bigchar = COLOR_PAIR(alt_pair);
           else
               *ptr_bigchar = COLOR_PAIR(reg_pair);
#ifdef DEBUG
           printf(" digit AFTER   => %#018"PRIx64"\n", *ptr_bigchar);
#endif
       }
   }

   if (sign)
       *ptr_bigchar = COLOR_PAIR(reg_pair);

   return;
}


int  ACCEPT_NUMERIC(void *a, void *b)
{

    cob_field  *f1   = cob_get_param_field (1, "PDTEST3");
    cob_field  *comm = cob_get_param_field (2, "PDTEST3");

  return (cob_accept_numeric(f1, comm));
}

void DUMP_HEX(void *source, int len)
{
   unsigned char   *ptr;
   int             cntr;
   ptr             = (unsigned char *)source;

// printf(" length in DUMP_HEX is ==> %d \n", len);

   if (len > 48)
       len = 48;

   printf("  Hex Dump ==>  ");
   for(cntr = 0; cntr < len; cntr++, ptr++)
   {
     printf("%02X", *ptr);
   }
   printf(" <== \n");
}



void DUMP(void *source, int *len)
{
   unsigned char   *ptr;
   int             cntr, len1;
   ptr             = (unsigned char *)source;

   len1 = *len;
   printf(" length in DUMP_HEX is ==> %d \n", len1);

   if (len1 > 48)
       len1 = 48;

   printf("  Hex Dump ==>  ");
   for(cntr = 0; cntr < len1; cntr++, ptr++)
   {
     printf("%02X", *ptr);
   }
   printf(" <== \n");
}


void START_TIME()
{

   start_time = clock();
}


void END_TIME()
{

   end_time = clock();
   elapsed_time = end_time - start_time;
   printf(" Elapsed time is ==> %lu  \n", elapsed_time);
}


