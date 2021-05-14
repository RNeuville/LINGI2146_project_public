#include "contiki.h"
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include <stdio.h>
#include <stdlib.h>

#include "dev/leds.h"
#include "sys/log.h"
#define LOG_MODULE "App"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define REMOTE_SERVER_PORT 5678

static struct simple_udp_connection udp_connection;

uint8_t state = 0;
uint8_t ring = 0;

PROCESS(alarm_mote, "Alarm Mote");
AUTOSTART_PROCESSES(&alarm_mote);


//creation of a LinkedList which stores the ack the alarm is waiting
struct node {
    uip_ipaddr_t ip_addr;
    uint8_t token1;
    uint8_t token2;
    clock_time_t t;
    struct node *next;
};

uint8_t random_token_2bits(){
     return (uint8_t) rand()%3;
}

uint8_t random_token_8bits(){
     return (uint8_t) rand()%256;
}


struct node *head = NULL;
struct node *current = NULL;

// Insertion of the Ack in the Structure
void insertFirst(uip_ipaddr_t ip_addr, uint8_t token1, uint8_t token2,clock_time_t t) {
   struct node *link = (struct node*) malloc(sizeof(struct node));
	
   link->ip_addr = ip_addr;
   link->token1 = token1;
   link->token2 = token2;
   link->t = t;

   link->next = head;

   head = link;
}

// Deletion of the Ack in the Structure
void delete(const uip_ipaddr_t* ip_addr_1, uint8_t token1, uint8_t token2) {

   struct node* current = head;
   struct node* previous = NULL;
	
   if(head != NULL) {
        while(!uip_ipaddr_cmp(&(current->ip_addr),ip_addr_1) && !(current-> token1 != token1) && !(current->token2 != token2)) {

            if(current->next != NULL) {
                previous = current;
                current = current->next;
            }
            else{
                return;
            }
        }
    

        if(current == head) {
     
            head = head->next;
        } else {
            previous->next = current->next;
        }
   }
}

// Resend the pkt when the timer has timeout without any ack receive
void resend_ack(const uip_ipaddr_t ip_addr, uint8_t token1, uint8_t token2){
    
    delete(&ip_addr,token1,token2);

    clock_time_t ack_timer=  clock_time() + (30*CLOCK_SECOND);
    insertFirst(ip_addr,token1,token2,ack_timer);    
        
    uint8_t buffer[3];
    uint8_t answer = 1 << 5 | 1 << 4 | 1 << 3;

    answer = answer | token1;
    buffer[0] = answer;
        
    buffer[1] = token2;

    simple_udp_sendto(&udp_connection, buffer, 3, &ip_addr);
}

static void
udp_callback(struct simple_udp_connection *c,
            const uip_ipaddr_t *sender_addr,
            uint16_t sender_port,
            const uip_ipaddr_t *receiver_addr,
            uint16_t receiver_port,
            const uint8_t *data,
            uint16_t datalen)
{
    char* message = (char*) data;

    // 4 bits which determine the code
    uint8_t code = message[0] >> 4;

    // Ackable Flag
    uint8_t ackable = message[0]<<4;
    ackable = ackable >> 7;

    // Payload Flag
    uint8_t has_payload = message[0] << 5;
    has_payload = has_payload >> 7;

    //the first 2 bit of the token
    uint8_t token_1 = message[0] << 6;
    token_1 = token_1 >> 6;

    //the other 8 bit of the token
    uint8_t token_2 = message[1];

    uint8_t payload = 0;

    if(has_payload == 1){ 
        payload = message[2];
    }

    const uip_ipaddr_t *sender_addr_copy = sender_addr;


    if(ackable == 1){ // Return an Ack if requested
        uint8_t buffer[3];

        uint8_t answer = 1 << 4;
        answer = answer | token_1;

        buffer[0] = answer;
        buffer[1] = token_2;

	    simple_udp_sendto(&udp_connection, buffer, 3, sender_addr);
    }


    if (code == 0){ // Return an adequate pkt with the sensor id

        uint8_t buffer[3];

        uint8_t answer = 1 << 2;
        answer = answer | token_1;

        buffer[0] = answer;
        buffer[1] = token_2;
        buffer[2] = (uint8_t) 4;

	    simple_udp_sendto(&udp_connection, buffer, 3, sender_addr);
    }

    if(code == 1){ // Ack receive
        delete(sender_addr,token_1,token_2);
    }

    if (code == 2){ // Set the State according to the payload
        if( has_payload == 0){
            if (state == 1){
                state = 0;
            }
            else{
                state = 1;
            }
        }
        else if( payload == 1 || payload == 0){
            state = payload;
        }
    }

    if (code == 3){ // Send to the server That the alarm is ringing

        uip_ipaddr_t motion_detector_ip;
        uip_ip6addr(&motion_detector_ip,0xfe80,0,0,0,0xc30c,0,0,3);

        uip_ipaddr_t interface_ip;
        uip_ip6addr(&interface_ip,0xfd00,0,0,0,0,0x0242,0xac11,3);


        if(uip_ipaddr_cmp(sender_addr, sender_addr_copy)){
            if (state == 1 && ring == 0){ //sending that the alarm is ringing

                ring = 1;

                uint8_t r_token1 = random_token_2bits();
                uint8_t r_token2 = random_token_8bits();

                uint8_t buffer[3];

                uint8_t answer = 1 << 5 | 1 << 4 | 1 << 3 | 1 << 2;
                answer = answer | r_token1;

                buffer[0] = answer;
                buffer[1] = r_token2;
                buffer[2] = (uint8_t) 1;

                clock_time_t ack_timer = clock_time() + (30*CLOCK_SECOND);
                insertFirst(interface_ip,r_token1,r_token2,ack_timer);
                
	            simple_udp_sendto(&udp_connection, buffer, 3, &interface_ip);
            }
        }
        if(has_payload == 1){
            if(state == 1){
                ring = payload;
            }
        }
    }
}
PROCESS_THREAD(alarm_mote, ev, data)
{
    PROCESS_BEGIN();

    simple_udp_register(&udp_connection, UDP_CLIENT_PORT, NULL, REMOTE_SERVER_PORT, udp_callback);
    while(1){


	    static struct etimer et;
        etimer_set(&et, CLOCK_SECOND*10);

        PROCESS_WAIT_EVENT();


	    if(etimer_expired(&et)) {

            if( ring == 1 && state == 1){
                leds_on(LEDS_GREEN); // ALarm is Ringing
            }
            else if (ring == 0 || state == 0){
                leds_off(LEDS_GREEN); // Alarm not ringing
            }

            struct node* current = head;
            
            if(head != NULL) {
                while(current !=  NULL){

                     //when ack timer is timeout ==> Resend Ack
                    if(current->t > clock_time()){
                        resend_ack(current->ip_addr,current->token1,current->token2);
                        current = current -> next;
                    }
                    current = current -> next;

                }
            }
        }
    }

    PROCESS_END();
}

    
