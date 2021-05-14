#include "contiki.h"
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include <stdio.h>
#include <stdlib.h>

#include "sys/log.h"
#define LOG_MODULE "App"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define REMOTE_SERVER_PORT 5678


static struct simple_udp_connection udp_connection;

uip_ipaddr_t interface_ip;

uint8_t humidity = 48;

PROCESS(humidity_mote, "Humidity Mote");
AUTOSTART_PROCESSES(&humidity_mote);

uint8_t rand_humidity(){
    return  (uint8_t) rand() % 50 +10;
}

uint8_t random_token_2bits(){
     return (uint8_t) rand()%3;
}

uint8_t random_token_8bits(){
     return (uint8_t) rand()%256;
}


//Change the value of the Humidity sensor and send it back with an adequate pkt to the Server
void send_new_humidity(){

    uip_ip6addr(&interface_ip,0xfd00,0,0,0,0,0x0242,0xac11,3);

    humidity = rand_humidity();

    uint8_t buffer[3];

    uint8_t answer = 1 << 5 | 1 << 2;
    answer = answer | random_token_2bits();

    buffer[0] = answer;
    buffer[1] = random_token_8bits();
    buffer[2] = (uint8_t) humidity;

    simple_udp_sendto(&udp_connection, buffer,3, &interface_ip);
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
    
    if(ackable == 1){  // Return an Ack if requested

        uint8_t buffer[3];

        uint8_t answer = 1 << 4;
        answer = answer | token_1;

        buffer[0] = answer;
        buffer[1] = token_2;

	    simple_udp_sendto(&udp_connection, buffer, 3, sender_addr);

    }

    if(code == 0){ // Return an adequate pkt with the sensor id

        uint8_t buffer[3];
        
        uint8_t answer = 1 <<2;
        answer = answer | token_1;
        
        buffer[0] = answer;
        buffer[1] = token_2;
        buffer[2] = (uint8_t) 2;

	    simple_udp_sendto(&udp_connection, buffer, 3, sender_addr);
    }

    if(code == 2){ // Return an adequate pkt with the Humidity value

        uint8_t buffer[3];
        
        uint8_t answer = 1 << 5 | 1 <<2;
        answer = answer | token_1;

        buffer[0] = answer;
        buffer[1] = token_2;
        buffer[2] = (uint8_t) humidity;

        simple_udp_sendto(&udp_connection, buffer, 3, sender_addr);
    }
}
PROCESS_THREAD(humidity_mote, ev, data)
{
    PROCESS_BEGIN();

    uip_ip6addr(&interface_ip,0xfd00,0,0,0,0,0x0242,0xac11,3);

    simple_udp_register(&udp_connection, UDP_CLIENT_PORT, NULL, REMOTE_SERVER_PORT, udp_callback);

    while(1){
        static struct etimer et;
        etimer_set(&et, CLOCK_SECOND*60); //change the Humidity Value each 60 seconds

        PROCESS_WAIT_EVENT();


	    if(etimer_expired(&et)) {
            send_new_humidity();
        }

    }

    PROCESS_END();
}