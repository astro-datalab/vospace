--
-- Table structure for table `capabilities`
--

CREATE TABLE `capabilities` (
  `identifier` varchar(4096) DEFAULT NULL,
  `capability` varchar(128) DEFAULT NULL,
  `active` int(4) DEFAULT NULL,
  INDEX cap_id_idx (`identifier`(767)),
  INDEX cap_cap_idx (`capability`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `jobs`
--

CREATE TABLE `jobs` (
  `identifier` varchar(128) NOT NULL,
  `type` varchar(45) NOT NULL,
  `userid` varchar(128) DEFAULT NULL,
  `phase` varchar(45) NOT NULL,
  `method` varchar(45) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `completed` datetime DEFAULT NULL,
  `resultid` varchar(45) DEFAULT NULL,
  `job` text,
  PRIMARY KEY (`identifier`),
  INDEX job_typ_idx (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `links`
--

CREATE TABLE `links` (
  `identifier` varchar(4096) NOT NULL,
  `target` varchar(4096) DEFAULT NULL,
  KEY `lnk_id_idx` (`identifier`(250)),
  KEY `lnk_tgt_idx` (`target`(250))
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `listings`
--

CREATE TABLE `listings` (
  `token` varchar(128) NOT NULL,
  `offset` int(11) DEFAULT '0',
  `count` int(11) DEFAULT '0',
  `updateDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `whereQuery` text,
  PRIMARY KEY (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `metaproperties`
--

CREATE TABLE `metaproperties` (
  `identifier` varchar(128) NOT NULL,
  `type` smallint(6) DEFAULT '0',
  `readonly` smallint(6) DEFAULT '0',
  PRIMARY KEY (`identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `results`
--

CREATE TABLE `results` (
  `identifier` varchar(128) NOT NULL,
  `details` text,
  PRIMARY KEY (`identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `transfers`
--
CREATE TABLE `transfers` (
  `identifier` int(11) NOT NULL AUTO_INCREMENT,
  `jobid` varchar(128) DEFAULT NULL,
  `rendpoint` varchar(4096) NOT NULL,
  `created` datetime DEFAULT NULL,
  `completed` datetime DEFAULT NULL,
  PRIMARY KEY (`identifier`),
  KEY `tra_rend_idx` (`rendpoint`(40)),
  KEY `tra_jid_idx` (`jobid`)
) ENGINE=InnoDB AUTO_INCREMENT=259176 DEFAULT CHARSET=latin1;

--
-- Table structure for table `nodes`
--

CREATE TABLE `nodes` (
  `identifier` varchar(4096) NOT NULL,
  `depth` tinyint(4) DEFAULT '-1',
  `type` tinyint(4) NOT NULL,
  `view` varchar(128) DEFAULT NULL,
  `status` smallint(6) DEFAULT '0',
  `owner` varchar(128) DEFAULT NULL,
  `location` varchar(4096) DEFAULT NULL,
  `creationDate` datetime DEFAULT NULL,
  `lastModificationDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `nod_dep_idx` (`depth`),
  KEY `nod_typ_idx` (`type`),
  KEY `nod_own_id_idx` (`owner`,`identifier`(250)),
  KEY `nod_own_dep_id_idx` (`owner`,`depth`,`identifier`(250)),
  KEY `nod_id_idx` (`identifier`(250)),
  KEY `nod_loc_idx` (`location`(250))
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `addl_props`
--

CREATE TABLE `addl_props` (
  `identifier` varchar(4096) NOT NULL,
  `property` varchar(128) NOT NULL,
  `value` varchar(256) NOT NULL,
  KEY `add_id_idx` (`identifier`(767))
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
