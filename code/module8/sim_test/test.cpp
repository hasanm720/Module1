#include "Arduino.h"
#include <vector>
#include <map>
#include <sstream>
unsigned long simMicros=0; SerialT Serial;
#include "sketch.cpp"
// Plant: pin -> temperature; TEC relaxes toward Module 4 steady state; rods lag it.
std::map<int,double> T={{A0,22},{A1,22},{A2,22},{A3,22},{A4,22},{A5,22}};
int heat=0,cool=0; int overlap=0; bool frozen=false; bool nanTec=false;
void pinMode(int,int){}
void analogWrite(int p,int v){ if(p==9)heat=v; if(p==10)cool=v; if(heat>0&&cool>0)overlap++; }
int analogRead(int pin){
  simMicros+=112;
  double t=T[pin];
  if(pin==A1&&nanTec) return 1023;
  double R=100000.0*exp(3950.0*(1/(t+273.15)-1/298.15));
  return (int)lround(1023.0*R/(R+100000.0));
}
void stepPlant(double dt){
  if(frozen) return;
  double u=heat-cool; double ss= u>=0? 22+0.5311*u : 22+0.1878*u;
  T[A1]+= (ss-T[A1])*dt/30.0;
  T[A5]+= (T[A1]-5-T[A5])*dt/40.0;
}
std::string lastRec; int recs=0; std::vector<std::string> events;
void pump(double seconds,bool ping=true){
  unsigned long end=simMicros+(unsigned long)(seconds*1e6); unsigned long nextPing=simMicros;
  while(simMicros<end){
    unsigned long t0=simMicros;
    if(ping&&simMicros>=nextPing){for(char c:std::string("PING\n"))Serial.in.push_back(c); nextPing=simMicros+500000;}
    loop();
    stepPlant((simMicros-t0)/1e6);
    size_t n; while((n=Serial.out.find('\n'))!=std::string::npos){
      std::string l=Serial.out.substr(0,n); Serial.out.erase(0,n+1);
      if(l.rfind("EVENT",0)==0) events.push_back(l); else {lastRec=l;recs++;}
    }
  }
}
void cmd(const std::string&s){for(char c:s)Serial.in.push_back(c);Serial.in.push_back('\n');}
std::vector<std::string> f(const std::string&l){std::vector<std::string> r;std::stringstream s(l);std::string x;while(getline(s,x,','))r.push_back(x);return r;}
int fails=0;
void check(bool ok,const char*what){printf("%s  %s\n",ok?"PASS":"FAIL",what); if(!ok)fails++;}
std::string state(){return f(lastRec)[1];}
int pwm(){return atoi(f(lastRec).back().c_str());}
int main(){
  setup(); check(Serial.out.rfind("time_ms,run_state",0)==0,"header printed");
  Serial.out.clear();
  pump(3); check(state()=="IDLE"&&pwm()==0&&heat==0&&cool==0,"startup idle, output zero");
  check(f(lastRec).size()==18,"record has 18 fields");
  cmd("START"); pump(1); check(state()=="IDLE"&&heat==0,"START with empty schedule refused");
  events.clear();
  cmd("STEP 600 40 16 50"); pump(1); cmd("STEP 600 45 16 100"); pump(1); cmd("STEP 600 20 11 100"); pump(1); cmd("STEP 0 40 16 100"); pump(1);
  cmd("STEP 600 40 16 100 9"); pump(1); cmd("STEP 600 40"); pump(1);
  int rej=0; for(auto&e:events) if(e.find("REJECT")!=std::string::npos) rej++;
  check(rej==6,"bad steps rejected: period<100, >56 C, <10 C, zero duration, extra field, missing field");
  check(stepCount==0,"no bad step stored");
  // Full PI run: 2 steps, period change mid-run.
  cmd("MODE PI"); cmd("GAINS 16 0.5"); cmd("STEP 300 40 8 100"); cmd("STEP 300 40 8 200"); pump(1);
  cmd("START"); double maxJump=0,prev=NAN,prevT=0; int maxP=0; bool sawStep2=false; 
  for(int i=0;i<850;i++){ pump(0.68); auto r=f(lastRec); if(r[1]!="RUN")break; double sp=atof(r[7].c_str()); double tm=atof(r[0].c_str())/1000; if(std::isfinite(prev)&&tm>prevT) maxJump=fmax(maxJump,fabs(sp-prev)/(tm-prevT)); prev=sp; prevT=tm; maxP=std::max(maxP,abs(pwm())); if(r[3]=="2")sawStep2=true; }
  check(sawStep2,"schedule advanced to step 2 automatically");
  printf("     max setpoint rate %.4f C/s (limit for 8 C at 100 s: %.4f)\n",maxJump,8*2*PI/100);
  check(maxJump<8*2*PI/100*1.02,"setpoint continuous across the period change");
  check(state()=="DONE"&&heat==0&&cool==0,"schedule finishes DONE with zero output");
  check(overlap==0,"HEAT and COOL never on together");
  int steps_ev=0; for(auto&e:events) if(e.find(",STEP,")!=std::string::npos) steps_ev++;
  check(steps_ev==2,"STEP event printed at each transition");
  // Cooling multiplier before saturation: P mode, TEC above setpoint.
  T[A1]=30; frozen=true; cmd("CLEAR"); cmd("MODE P"); cmd("GAINS 10 0"); cmd("RATIO 2.5"); cmd("STEP 100 20 0 100"); pump(1);
  cmd("START"); pump(2); auto r=f(lastRec);
  printf("     P mode e=-10: controller_pwm %s signed %s\n",r[15].c_str(),r.back().c_str());
  check(fabs(atof(r[15].c_str())+100)<0.5&&pwm()==(int)lround(2.5*atof(r[15].c_str()))&&cool==-pwm()&&heat==0,"negative command x r, COOL pin used");
  T[A1]=40; pump(1.5); r=f(lastRec); check(pwm()==-255,"saturates at -255 after the multiplier");
  cmd("GAINS 1 1"); pump(1); check(state()=="STOPPED"&&heat==0&&cool==0,"settings change during a run stops it");
  frozen=false;
  // Timeout.
  T[A1]=22; T[A5]=22; cmd("CLEAR"); cmd("MODE PI"); cmd("GAINS 16 0.5"); cmd("RATIO 2.83"); cmd("STEP 600 40 8 100"); pump(1); cmd("START"); pump(5);
  check(state()=="RUN"&&heat>0,"run is heating with heartbeat");
  pump(3.5,false); check(state()=="TIMEOUT"&&heat==0&&cool==0,"no heartbeat: TIMEOUT, output zero");
  // Rod-base limit.
  cmd("START"); pump(3); frozen=true; T[A5]=56.5; pump(2); check(state()=="ROD_LIMIT"&&heat==0&&cool==0,"T1 > 56 C: ROD_LIMIT, output zero");
  T[A5]=25; cmd("START"); pump(3); T[A5]=-300; 
  // TEC shutdown.
  T[A5]=25; check(state()=="RUN","restarts after rod recovers");
  T[A1]=60.5; pump(2); check(state()=="SHUTDOWN"&&heat==0&&cool==0,"TEC > 60 C: SHUTDOWN, output zero");
  cmd("START"); pump(1.5); check(state()=="SHUTDOWN"&&heat==0,"START refused while TEC over limit");
  T[A1]=30; pump(1.5); check(state()=="IDLE"&&heat==0,"recovers to IDLE, stays off until START");
  cmd("START"); pump(2); nanTec=true; pump(2); check(state()=="SENSOR_FAULT"&&heat==0&&cool==0,"TEC sensor fault: output zero");
  nanTec=false; pump(2);
  // Open loop table.
  cmd("CLEAR"); cmd("MODE OPEN"); cmd("STEP 100 45 0 100"); pump(1); cmd("START"); pump(3); r=f(lastRec);
  printf("     OPEN at 45 C: feedforward %s controller %s ratio %s signed %s\n",r[8].c_str(),r[15].c_str(),r[16].c_str(),r.back().c_str());
  check(pwm()==43&&r[15]=="nan","OPEN at 45 C uses Module 4 PWM 43; unused fields are nan");
  cmd("BOGUS"); pump(1.5); check(state()=="STOPPED"&&heat==0,"unknown command during a run stops it");
  cmd("START"); pump(2); cmd("STOP"); pump(1.5); check(state()=="STOPPED"&&heat==0&&cool==0,"STOP zeroes output");
  // HOLD / NEXT.
  events.clear(); cmd("HOLD ON"); cmd("CLEAR"); cmd("MODE PI"); cmd("STEP 120 40 8 100"); cmd("STEP 120 40 8 200"); pump(1);
  cmd("START"); pump(200); r=f(lastRec);
  check(state()=="RUN"&&r[3]=="1","HOLD ON: step 1 kept past its 120 s duration");
  double sp1=atof(r[7].c_str()), t1=atof(r[0].c_str())/1000;
  cmd("NEXT"); pump(1.5); r=f(lastRec);
  check(state()=="RUN"&&r[3]=="2","NEXT moves to step 2 during the run");
  double rate=fabs(atof(r[7].c_str())-sp1)/(atof(r[0].c_str())/1000-t1);
  check(rate<8*2*PI/100*1.05,"setpoint continuous across NEXT");
  bool sawNext=false; for(auto&e:events) if(e.find(",NEXT,")!=std::string::npos) sawNext=true;
  check(sawNext,"NEXT printed as an event");
  pump(300); check(state()=="RUN"&&f(lastRec)[3]=="2","HOLD still applies on the last step");
  cmd("HOLD OFF"); pump(2); check(state()=="DONE"&&heat==0&&cool==0,"HOLD OFF past duration: run ends DONE, output zero");
  cmd("START"); pump(2); cmd("NEXT"); pump(1.5); cmd("NEXT"); pump(1.5);
  check(state()=="DONE"&&heat==0&&cool==0,"NEXT on the last step ends DONE with zero output");
  cmd("NEXT"); pump(1.5); check(state()=="DONE","NEXT while idle is rejected, not started");
  check(overlap==0,"HEAT and COOL never on together (whole test)");
  printf("\n%d failure(s)\n",fails); return fails;
}
