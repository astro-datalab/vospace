--
-- Insert data from the old VOSpace schema into the new schema
--

INSERT INTO capabilities SELECT * from vospace.capabilities;
INSERT INTO jobs SELECT * from vospace.jobs;
INSERT INTO listings SELECT * from vospace.listings;
INSERT INTO results SELECT * from vospace.results;
INSERT INTO transfers SELECT * from vospace.transfers;
INSERT INTO nodes (identifier, type, view, status, owner, location, creationDate, lastModificationDate)
    SELECT identifier, type, view, status, owner, location, creationDate, lastModificationDate from vospace.nodes;
UPDATE nodes SET depth = (LENGTH(identifier)-LENGTH(REPLACE(identifier,'/',''))-3);
