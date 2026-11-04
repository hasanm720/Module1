#pragma once
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <deque>
using std::isfinite;
typedef uint8_t byte;
#define PI 3.14159265358979
#define OUTPUT 1
#define A0 14
#define A1 15
#define A2 16
#define A3 17
#define A4 18
#define A5 19
#define constrain(x,a,b) ((x)<(a)?(a):((x)>(b)?(b):(x)))
class __FlashStringHelper;
#define F(s) (reinterpret_cast<const __FlashStringHelper*>(s))
extern unsigned long simMicros;
inline unsigned long millis(){return simMicros/1000;}
void pinMode(int,int);
void analogWrite(int,int);
int analogRead(int);
struct SerialT{
  std::string out; std::deque<char> in;
  void begin(long){}
  int available(){return in.size();}
  int read(){char c=in.front();in.pop_front();return c;}
  void print(const __FlashStringHelper*s){out+=(const char*)s;}
  void print(const char*s){out+=s;}
  void print(char c){out+=c;}
  void print(int v){out+=std::to_string(v);}
  void print(unsigned long v){out+=std::to_string(v);}
  void print(float v,int d){char b[40];snprintf(b,40,"%.*f",d,v);out+=b;}
  void println(const __FlashStringHelper*s){print(s);out+="\n";}
  void println(const char*s){print(s);out+="\n";}
  void println(int v){print(v);out+="\n";}
  void println(float v,int d){print(v,d);out+="\n";}
};
extern SerialT Serial;
