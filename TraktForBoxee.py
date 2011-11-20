#!/usr/bin/env python

import logging
import ConfigParser
import boxeeboxclient
import TraktClient
import sys
import time

VERSION = "1.0"
BOXEE_VERSION = BOXEE_DATE = ""
TIMER_INTERVAL = 10

class TraktForBoxee(object):
    
    def __init__(self):
        logging.basicConfig(format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
                            level=logging.DEBUG,
                            stream=sys.stdout)
        
        self.log = logging.getLogger("TraktForBoxee")
        self.log.debug("Initialized Trakt for Boxee.")
        
        self.config = ConfigParser.RawConfigParser()
        self.config.read("settings.cfg")
        
        boxee_ip = self.config.get("Boxee", "IP")
        boxee_port = self.config.getint("Boxee", "Port")
        
        self.boxee_client = boxeeboxclient.BoxeeBoxClient("9001",
                                                          boxee_ip,
                                                          boxee_port,
                                                          "traktforboxee",
                                                          "Trakt for Boxee")
        
        trakt_api = "f46fbebb833fbeb8196b69e0e8d5de8f852b7ea6"
        trakt_username = self.config.get("Trakt", "Username")
        trakt_password = self.config.get("Trakt", "Password")
        
        self.trakt_client = TraktClient.TraktClient(trakt_api,
                                                    trakt_username,
                                                    trakt_password)
        
        build_info = self.boxee_client.getInfoLabels(["System.BuildVersion",
                                                      "System.BuildDate"])
        BOXEE_VERSION = build_info["System.BuildVersion"]
        BOXEE_DATE = build_info["System.BuildDate"]
        
        self.SCROBBLE_TV = self.config.getboolean("TraktForBoxee", "ScrobbleTV")
        self.SCROBBLE_MOVIE = self.config.getboolean("TraktForBoxee", "ScrobbleMovie")
        self.NOTIFY_BOXEE = self.config.getboolean("TraktForBoxee", "NotifyBoxee")
        
        self.scrobbled = False
        self.watching_now = ""
        
        self.run()
        
        #self.log.debug(self.boxee_client.getCurrentlyPlaying())
        
        #t = self.client.callMethod("System.GetInfoLabels", {'labels': ['VideoPlayer.Title', 'VideoPlayer.TVShowTitle', 'VideoPlayer.Season', 'VideoPlayer.Time', 'VideoPlayer.Year']}, True);
        #t = self.client.callMethod("VideoPlayer.GetPercentage")
        #self.log.debug(t["result"])
        #self.log.debug(int(self.boxee_client.getVideoPlayerPercentage()))
        #print self.client.getActivePlayers()
        #self.client = bbc.BoxeeBoxClient("57", "192.168.1.148", 9090, "traktforboxee", "Trakt for Boxee")
    
    def run(self):
        timer = 0
        while (True):
            timer += TIMER_INTERVAL
            status = self.boxee_client.getCurrentlyPlaying()
            
            tv = status["type"] == "tv"
            
            if (status["type"] == "none"):
                self.log.debug("Boxee not playing anything, sleep.")
                time.sleep(TIMER_INTERVAL)
                continue
                
            watching_now = status["title"] + status["year"] + status["episode"] + status["season"] + status["episode_title"] + str(status["duration"])
            if (self.watching_now != watching_now):
                self.watching_now = watching_now
                self.scrobbled = False
                self.log.debug("Now watching something else, cancel currently watching.")
                self.trakt_client.cancelWatching()
                timer = 900 #Set watching first round through please
            
            if ((tv and not self.SCROBBLE_TV) or
                (not tv and not self.SCROBBLE_MOVIE)):
                self.log.debug("Set to ignore this media type, doing so.")
                time.sleep(TIMER_INTERVAL)
            
            if (status["percentage"] >= 90
                and not self.scrobbled):
                    self.log.debug("WE ARE SCROBBLING!")
                    if (self.NOTIFY_BOXEE):
                        self.boxee_client.showNotification("Scrobbling to Trakt!")
                    self.scrobbled = True
                    
                    self.trakt_client.update_media_status(status["title"],
                                                          status["year"],
                                                          status["duration"],
                                                          status["percentage"],
                                                          VERSION,
                                                          BOXEE_VERSION,
                                                          BOXEE_DATE,
                                                          tv=tv,
                                                          scrobble=True,
                                                          season=status["season"],
                                                          episode=status["episode"])
                    
            elif (status["percentage"] < 90
                  and not self.scrobbled
                  and timer >= 900):
                self.log.debug("WE ARE UPDATING WATCHING STATUS!")
                timer = 0
                
                self.boxee_client.showNotification("Watching on Trakt!")
                self.trakt_client.update_media_status(status["title"],
                                                      status["year"],
                                                      status["duration"],
                                                      status["percentage"],
                                                      VERSION,
                                                      BOXEE_VERSION,
                                                      BOXEE_DATE,
                                                      tv=tv,
                                                      season=status["season"],
                                                      episode=status["episode"])
            
            
            self.log.debug("NOT SCROBBLING... " + str(timer))
            time.sleep(TIMER_INTERVAL)
                
        
if __name__ == '__main__':
    test = TraktForBoxee()