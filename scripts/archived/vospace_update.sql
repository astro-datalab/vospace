

CREATE INDEX nod_own_id_idx on nodes (owner(25), identifier(250));
CREATE INDEX nod_own_dep_id_idx on nodes (owner(25), depth, identifier(250));

-- Make location and indentifier indices more compact.
-- Originally we make the indices of 764 bytes long but
-- I can't find a location or identifier longer than
-- 225, so setting it to 250 saves quite a bit of space
-- and should traverse memory pages slighly faster.
-- DROP INDEX nod_id_idx on nodes;
-- CREATE INDEX nod_id_idx on nodes (identifier(250));
-- DROP INDEX nod_loc_idx on nodes;
-- CREATE INDEX nod_loc_idx on nodes (location(250));

-- Possibly drop the following indices
-- DROP INDEX nod_own_idx on nodes;
-- DROP INDEX nod_dep_idx on nodes;
-- DROP INDEX nod_typ_idx on nodes;


CREATE TABLE `rtransfers` (
  `identifier` int(11) NOT NULL AUTO_INCREMENT,
  `jobid` varchar(128) DEFAULT NULL,
  `rendpoint` varchar(4096) NOT NULL,
  `created` datetime DEFAULT NULL,
  `completed` datetime DEFAULT NULL,
  PRIMARY KEY (`identifier`),
  KEY `tra_rend_idx` (`rendpoint`(40)),
  KEY `tra_jid_idx` (`jobid`)
) ENGINE=InnoDB AUTO_INCREMENT=1931 DEFAULT CHARSET=latin1;

INSERT INTO rtransfers select identifier, jobid, reverse(endpoint), created, completed from transfers;

RENAME TABLE transfers to transfers_old;

RENAME TABLE rtransfers to transfers;

-- Manually drop old transfers table
-- DROP TABLE transfers_old;
